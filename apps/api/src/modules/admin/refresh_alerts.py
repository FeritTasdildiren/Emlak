"""
Emlak Teknoloji Platformu - Admin Refresh Alerts Router

Veri yenileme alert'leri ve durum izleme admin endpoint'leri.

Prefix: /admin/refresh
Guvenlik: Tum endpoint'ler JWT + platform_admin rolu gerektirir.
          PUBLIC_PATHS'e EKLENMEZ — TenantMiddleware JWT dogrulamasi zorunlu.

Endpoint'ler:
    GET    /admin/refresh/status              → Tum tablolarin refresh durumu ozet
    GET    /admin/refresh/alerts              → Aktif alert'ler listesi
    POST   /admin/refresh/retry/{table}       → Manuel retry tetikle
    GET    /admin/refresh/history             → Son 24 saat refresh gecmisi

Referans: src/modules/admin/outbox_monitor_router.py (pattern), TASK-054
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from fastapi import APIRouter, Depends, HTTPException

from src.core.provenance import DEFAULT_STALE_THRESHOLD_DAYS
from src.core.sync_database import get_sync_session
from src.modules.auth.dependencies import require_role
from src.tasks.refresh_monitor import (
    NO_REFRESH_THRESHOLD,
    STALE_ALERT_PERCENT,
    STUCK_THRESHOLD_MINUTES,
)

logger = structlog.get_logger()

router = APIRouter(
    prefix="/admin/refresh",
    tags=["admin", "refresh-monitor"],
    dependencies=[Depends(require_role("platform_admin"))],
)

ALLOWED_TABLES = {"area_analyses", "deprem_risks"}


# ---------- GET /admin/refresh/status ----------


@router.get(
    "/status",
    summary="Tum tablolarin refresh durumu ozet",
    description="Area analyses ve deprem risks tablolarinin refresh status dagilimlari.",
)
async def get_refresh_status() -> dict[str, Any]:
    """
    Her tablo icin refresh_status dagiliminini dondurur.

    Icerdigi bilgiler:
        - Status bazli kayit sayilari (fresh, stale, refreshing, failed)
        - Son basarili refresh zamani
        - Toplam kayit sayisi
    """
    result: dict[str, Any] = {
        "collected_at": datetime.now(UTC).isoformat(),
        "tables": {},
    }

    for table in ALLOWED_TABLES:
        result["tables"][table] = _get_table_status(table)

    return result


# ---------- GET /admin/refresh/alerts ----------


@router.get(
    "/alerts",
    summary="Aktif alert'ler listesi",
    description="Stuck, failed, stale ve no-recent-refresh alert'leri.",
)
async def get_refresh_alerts() -> dict[str, Any]:
    """
    Tum aktif alert'leri dondurur.

    Alert turleri:
        - stuck_refresh: 30dk+ refreshing durumunda
        - failed_refresh: failed durumunda
        - stale_data: >%20 stale kayit
        - no_recent_refresh: 2x schedule period icerisinde refresh yok
    """
    alerts: list[dict[str, Any]] = []

    for table in ALLOWED_TABLES:
        _collect_alerts_for_table(table, alerts)

    return {
        "alert_count": len(alerts),
        "alerts": alerts,
        "collected_at": datetime.now(UTC).isoformat(),
    }


# ---------- POST /admin/refresh/retry/{table} ----------


@router.post(
    "/retry/{table}",
    summary="Manuel retry tetikle",
    description="area_analyses veya deprem_risks icin yenileme task'ini tetikle.",
)
async def trigger_refresh_retry(table: str) -> dict[str, Any]:
    """
    Belirtilen tablo icin veri yenileme task'ini kuyruge ekler.

    Args:
        table: "area_analyses" veya "deprem_risks"

    Returns:
        Task ID ve durum bilgisi.
    """
    if table not in ALLOWED_TABLES:
        raise HTTPException(
            status_code=400,
            detail=f"Gecersiz tablo: '{table}'. Gecerli: {', '.join(sorted(ALLOWED_TABLES))}",
        )

    task_map = {
        "area_analyses": "src.tasks.area_refresh.refresh_area_data",
        "deprem_risks": "src.tasks.deprem_risk_refresh.refresh_deprem_risk",
    }

    from src.celery_app import celery_app

    task_name = task_map[table]
    async_result = celery_app.send_task(task_name, queue="default")

    logger.info(
        "admin_refresh_retry_triggered",
        table=table,
        task_name=task_name,
        task_id=async_result.id,
    )

    return {
        "triggered": True,
        "table": table,
        "task_id": async_result.id,
        "task_name": task_name,
        "message": f"{table} yenileme task'i kuyruge eklendi.",
    }


# ---------- GET /admin/refresh/history ----------


@router.get(
    "/history",
    summary="Son 24 saat refresh gecmisi",
    description="Son 24 saat icinde guncellenen kayitlarin ozeti.",
)
async def get_refresh_history() -> dict[str, Any]:
    """
    Son 24 saat icindeki refresh aktivitesini dondurur.

    Her tablo icin:
        - Son 24 saatte guncellenen kayit sayisi
        - Basarili / basarisiz ayrimi
        - Son guncellenen kayit zamani
    """
    result: dict[str, Any] = {
        "period_hours": 24,
        "collected_at": datetime.now(UTC).isoformat(),
        "tables": {},
    }

    cutoff = datetime.now(UTC) - timedelta(hours=24)

    for table in ALLOWED_TABLES:
        try:
            with get_sync_session() as session:
                from sqlalchemy import text

                row = session.execute(
                    text(
                        "SELECT "
                        "  COUNT(*) FILTER (WHERE refresh_status = 'fresh' "
                        "    AND last_refreshed_at >= :cutoff) AS refreshed_ok, "
                        "  COUNT(*) FILTER (WHERE refresh_status = 'failed' "
                        "    AND updated_at >= :cutoff) AS refreshed_fail, "
                        "  MAX(last_refreshed_at) FILTER (WHERE refresh_status = 'fresh') AS last_ok "
                        f"FROM {table}"
                    ),
                    {"cutoff": cutoff},
                ).fetchone()

                result["tables"][table] = {
                    "refreshed_success": row[0] or 0 if row else 0,
                    "refreshed_failed": row[1] or 0 if row else 0,
                    "last_success_at": row[2].isoformat() if row and row[2] else None,
                }
        except Exception:
            logger.exception("refresh_history_query_failed", table=table)
            result["tables"][table] = {"error": "Sorgu basarisiz"}

    return result


# ─── Internal Helpers ──────────────────────────────────────────────────


def _get_table_status(table: str) -> dict[str, Any]:
    """Tek tablo icin status dagiliminini dondur."""
    try:
        with get_sync_session() as session:
            from sqlalchemy import text

            row = session.execute(
                text(
                    "SELECT "
                    "  COUNT(*) FILTER (WHERE refresh_status = 'fresh') AS fresh, "
                    "  COUNT(*) FILTER (WHERE refresh_status = 'stale') AS stale, "
                    "  COUNT(*) FILTER (WHERE refresh_status = 'refreshing') AS refreshing, "
                    "  COUNT(*) FILTER (WHERE refresh_status = 'failed') AS failed, "
                    "  COUNT(*) AS total, "
                    "  MAX(last_refreshed_at) FILTER (WHERE refresh_status = 'fresh') AS last_success "
                    f"FROM {table}"
                ),
            ).fetchone()

            if not row:
                return {"error": "Veri bulunamadi"}

            return {
                "fresh": row[0] or 0,
                "stale": row[1] or 0,
                "refreshing": row[2] or 0,
                "failed": row[3] or 0,
                "total": row[4] or 0,
                "last_success_at": row[5].isoformat() if row[5] else None,
            }
    except Exception:
        logger.exception("refresh_status_query_failed", table=table)
        return {"error": "Sorgu basarisiz"}


def _collect_alerts_for_table(
    table: str,
    alerts: list[dict[str, Any]],
) -> None:
    """Tek tablo icin alert'leri topla."""
    try:
        with get_sync_session() as session:
            from sqlalchemy import text

            row = session.execute(
                text(
                    "SELECT "
                    "  COUNT(*) FILTER (WHERE refresh_status = 'refreshing' "
                    "    AND last_refreshed_at < now() - interval '1 minute' * :stuck_min) AS stuck, "
                    "  COUNT(*) FILTER (WHERE refresh_status = 'failed') AS failed, "
                    "  COUNT(*) FILTER (WHERE refresh_status = 'stale' "
                    "    OR last_refreshed_at IS NULL "
                    "    OR last_refreshed_at < now() - interval '1 day' * :stale_days) AS stale, "
                    "  COUNT(*) AS total, "
                    "  MAX(last_refreshed_at) FILTER (WHERE refresh_status = 'fresh') AS last_success "
                    f"FROM {table}"
                ),
                {
                    "stuck_min": STUCK_THRESHOLD_MINUTES,
                    "stale_days": DEFAULT_STALE_THRESHOLD_DAYS,
                },
            ).fetchone()

            if not row:
                return

            stuck = row[0] or 0
            failed = row[1] or 0
            stale = row[2] or 0
            total = row[3] or 0
            last_success = row[4]

            if stuck > 0:
                alerts.append({
                    "type": "stuck_refresh",
                    "severity": "WARNING",
                    "table": table,
                    "detail": f"{stuck} kayit {STUCK_THRESHOLD_MINUTES}+ dk refreshing",
                    "count": stuck,
                })

            if failed > 0:
                alerts.append({
                    "type": "failed_refresh",
                    "severity": "ERROR",
                    "table": table,
                    "detail": f"{failed} kayit failed durumunda",
                    "count": failed,
                })

            if total > 0:
                stale_pct = (stale / total) * 100
                if stale_pct > STALE_ALERT_PERCENT:
                    alerts.append({
                        "type": "stale_data",
                        "severity": "WARNING",
                        "table": table,
                        "detail": f"Stale kayit orani %{stale_pct:.1f}",
                        "stale_percent": round(stale_pct, 1),
                    })

            threshold_days = NO_REFRESH_THRESHOLD.get(table, 14)
            if last_success is not None:
                days_since = (datetime.now(UTC) - last_success).days
                if days_since > threshold_days:
                    alerts.append({
                        "type": "no_recent_refresh",
                        "severity": "CRITICAL",
                        "table": table,
                        "detail": f"Son basarili refresh {days_since} gun once (esik: {threshold_days})",
                        "days_since_refresh": days_since,
                    })
            elif total > 0:
                alerts.append({
                    "type": "no_recent_refresh",
                    "severity": "CRITICAL",
                    "table": table,
                    "detail": "Hic basarili refresh kaydedilmemis",
                    "days_since_refresh": -1,
                })

    except Exception:
        logger.exception("refresh_alerts_query_failed", table=table)
