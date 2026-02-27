"""
Emlak Teknoloji Platformu - Refresh Status Monitor Task

Celery beat task: Veri yenileme durumunu periyodik kontrol et.
Stuck refresh (refreshing > 30dk) ve stale veri tespiti.

Beat Schedule: Her 30 dakikada bir (1800s)
Queue: default

Kontroller:
    1. refresh_status = "refreshing" ve last_refreshed_at > 30dk once → STUCK
    2. refresh_status = "failed" olan kayitlar → ALERT
    3. is_stale() == True olan kayitlar → STALE WARNING
    4. Son basarili refresh'ten bu yana gecen sure > threshold → ALERT

Tasarim:
    - Sync SQLAlchemy session (Celery worker — psycopg2)
    - OTel metrikleri refresh_metrics module uzerinden
    - structlog ile alert loglama
    - autoretry_for=() — monitoring task retry yapmasin, sonraki beat'te tekrar calisir

Referans: src/tasks/outbox_monitor_task.py (pattern), TASK-054
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text

from src.celery_app import celery_app
from src.core.provenance import DEFAULT_STALE_THRESHOLD_DAYS
from src.core.refresh_metrics import refresh_metrics
from src.core.sync_database import get_sync_session
from src.tasks.base import BaseTask

# ─── Thresholds ───────────────────────────────────────────────────────
STUCK_THRESHOLD_MINUTES: int = 30  # refreshing durumunda 30dk+ → stuck
STALE_ALERT_PERCENT: float = 20.0  # %20'den fazla stale kayit → alert
# Area: haftalik (7 gun), Deprem: aylik (31 gun). 2x = alert threshold.
NO_REFRESH_THRESHOLD: dict[str, int] = {
    "area_analyses": 14,   # 2 hafta
    "deprem_risks": 62,    # 2 ay
}


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="src.tasks.refresh_monitor.check_refresh_status",
    queue="default",
    soft_time_limit=60,
    time_limit=90,
    autoretry_for=(),
    max_retries=0,
)
def check_refresh_status(self: BaseTask) -> dict[str, Any]:
    """
    Her 30 dakikada calisir. Veri yenileme durumunu kontrol eder.

    Kontroller:
        1. STUCK: refresh_status = "refreshing" ve 30dk+ gecmis
        2. FAILED: refresh_status = "failed" olan kayitlar
        3. STALE: is_stale() == True kayit orani > %20
        4. NO_REFRESH: Son basarili refresh > 2x schedule period

    Returns:
        {
            "area_analyses": {"stuck": 0, "failed": 2, "stale": 5, "total": 100},
            "deprem_risks": {"stuck": 0, "failed": 0, "stale": 3, "total": 50},
            "alerts": [...]
        }
    """
    self.log.debug("refresh_monitor_started")

    alerts: list[dict[str, Any]] = []
    result: dict[str, Any] = {"alerts": alerts}

    for table in ("area_analyses", "deprem_risks"):
        table_stats = _check_table(self, table, alerts)
        result[table] = table_stats

    # ─── Alert ozeti logla ─────────────────────────────────────────
    if alerts:
        for alert in alerts:
            log_fn = self.log.error if alert["severity"] in ("ERROR", "CRITICAL") else self.log.warning
            log_fn(
                "refresh_alert",
                alert_type=alert["type"],
                severity=alert["severity"],
                table=alert["table"],
                detail=alert["detail"],
            )

    self.log.info(
        "refresh_monitor_completed",
        area_analyses=result.get("area_analyses"),
        deprem_risks=result.get("deprem_risks"),
        alert_count=len(alerts),
    )

    return result


def _check_table(
    task: BaseTask,
    table: str,
    alerts: list[dict[str, Any]],
) -> dict[str, int]:
    """Tek bir tablo icin tum kontrolleri calistir."""
    stats: dict[str, int] = {"stuck": 0, "failed": 0, "stale": 0, "total": 0}

    try:
        with get_sync_session() as session:
            # ─── 1) Status bazli sayilar ──────────────────────────
            row = session.execute(
                text(
                    "SELECT "
                    "  COUNT(*) FILTER (WHERE refresh_status = 'refreshing' "
                    "    AND last_refreshed_at < now() - interval '1 minute' * :stuck_min) AS stuck, "
                    "  COUNT(*) FILTER (WHERE refresh_status = 'failed') AS failed, "
                    "  COUNT(*) FILTER (WHERE refresh_status = 'stale' "
                    "    OR (last_refreshed_at IS NULL) "
                    "    OR (last_refreshed_at < now() - interval '1 day' * :stale_days)) AS stale, "
                    "  COUNT(*) AS total "
                    f"FROM {table}"
                ),
                {
                    "stuck_min": STUCK_THRESHOLD_MINUTES,
                    "stale_days": DEFAULT_STALE_THRESHOLD_DAYS,
                },
            ).fetchone()

            if row:
                stats["stuck"] = row[0] or 0
                stats["failed"] = row[1] or 0
                stats["stale"] = row[2] or 0
                stats["total"] = row[3] or 0

            # ─── 2) Son basarili refresh zamani ───────────────────
            last_success_row = session.execute(
                text(
                    "SELECT MAX(last_refreshed_at) "
                    f"FROM {table} "
                    "WHERE refresh_status = 'fresh'"
                ),
            ).fetchone()

            last_success_at = last_success_row[0] if last_success_row else None

        # ─── OTel metrikleri raporla ──────────────────────────────
        fresh_count = max(0, stats["total"] - stats["stale"] - stats["failed"] - stats["stuck"])
        refresh_metrics.record_status_counts(
            table=table,
            fresh=fresh_count,
            stale=stats["stale"],
            refreshing=stats["stuck"],  # stuck olanlar hala refreshing durumunda
            failed=stats["failed"],
        )

        # ─── 3) Alert uret ───────────────────────────────────────

        # STUCK REFRESH
        if stats["stuck"] > 0:
            alerts.append({
                "type": "stuck_refresh",
                "severity": "WARNING",
                "table": table,
                "detail": f"{stats['stuck']} kayit {STUCK_THRESHOLD_MINUTES}+ dk refreshing durumunda",
                "count": stats["stuck"],
            })

        # FAILED REFRESH
        if stats["failed"] > 0:
            alerts.append({
                "type": "failed_refresh",
                "severity": "ERROR",
                "table": table,
                "detail": f"{stats['failed']} kayit failed durumunda",
                "count": stats["failed"],
            })

        # STALE DATA (>%20)
        if stats["total"] > 0:
            stale_pct = (stats["stale"] / stats["total"]) * 100
            if stale_pct > STALE_ALERT_PERCENT:
                alerts.append({
                    "type": "stale_data",
                    "severity": "WARNING",
                    "table": table,
                    "detail": f"Stale kayit orani %{stale_pct:.1f} (>{STALE_ALERT_PERCENT}%)",
                    "stale_percent": round(stale_pct, 1),
                })

        # NO RECENT REFRESH
        threshold_days = NO_REFRESH_THRESHOLD.get(table, 14)
        if last_success_at is not None:
            days_since = (datetime.now(UTC) - last_success_at).days
            if days_since > threshold_days:
                alerts.append({
                    "type": "no_recent_refresh",
                    "severity": "CRITICAL",
                    "table": table,
                    "detail": (
                        f"Son basarili refresh {days_since} gun once "
                        f"(esik: {threshold_days} gun)"
                    ),
                    "days_since_refresh": days_since,
                })
        elif stats["total"] > 0:
            # Hic basarili refresh yok ama kayit var
            alerts.append({
                "type": "no_recent_refresh",
                "severity": "CRITICAL",
                "table": table,
                "detail": "Hic basarili refresh kaydedilmemis",
                "days_since_refresh": -1,
            })

    except Exception:
        task.log.exception("refresh_monitor_table_check_failed", table=table)

    return stats
