"""
Emlak Teknoloji Platformu - Drift Check Task

Celery Beat tarafindan gunluk olarak calistirilir.
PredictionLog verilerini analiz ederek drift tespiti yapar.

Schedule: Her gun 06:00 (Europe/Istanbul)
Queue: default

Mimari Karar:
    Sync psycopg2 kullanir (Celery worker'da async KULLANILMAZ).
    DriftMonitor async sinifinin islevselligini sync olarak tekrarlar.

Referans: TASK-067
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

from sqlalchemy import func, select

from src.celery_app import celery_app

if TYPE_CHECKING:
    from sqlalchemy.orm import Session
from src.core.sync_database import get_sync_session
from src.ml.drift_monitor import calculate_psi
from src.models.prediction_log import PredictionLog
from src.tasks.base import BaseTask


@celery_app.task(
    bind=True,
    base=BaseTask,
    queue="default",
    name="src.tasks.drift_check.check_drift",
    # Monitoring task — retry yapmasIn, bir sonraki beat'te tekrar calisir
    autoretry_for=(),
    max_retries=0,
)
def check_drift(self) -> dict[str, Any]:
    """
    Gunluk drift kontrolu.

    Celery Beat tarafindan her gun 06:00'da cagirilir.
    PredictionLog verilerini analiz eder ve drift durumunu loglar.
    Eger overall_status RED ise CRITICAL seviyede log uretir.

    Returns:
        dict: Drift raporu ozeti.
    """
    self.log.info("drift_check_started")

    try:
        with get_sync_session() as session:
            report = _build_drift_report_sync(session)
    except Exception:
        self.log.exception("drift_check_db_error")
        return {
            "overall_status": "UNKNOWN",
            "error": "Veritabani hatasi",
            "generated_at": datetime.now(UTC).isoformat(),
        }

    overall_status = report.get("overall_status", "UNKNOWN")
    alerts = report.get("alerts", [])
    stats = report.get("prediction_stats", {})

    self.log.info(
        "drift_check_completed",
        overall_status=overall_status,
        total_predictions=stats.get("total_predictions", 0),
        alert_count=len(alerts),
    )

    # Alert'leri logla
    for alert in alerts:
        level = alert.get("level", "INFO")
        log_kwargs = {
            "alert_level": level,
            "message": alert.get("message"),
            "metric": alert.get("metric"),
            "value": alert.get("value"),
        }
        if level == "CRITICAL":
            self.log.critical("drift_alert", **log_kwargs)
        else:
            self.log.warning("drift_alert", **log_kwargs)

    return report


# ======================================================================
# Sync Yardimci Fonksiyonlar (Celery worker icin)
# ======================================================================


def _build_drift_report_sync(session: Session) -> dict:
    """Sync session ile tam drift raporu olustur."""
    input_dist = _check_input_distribution_sync(session)
    confidence = _check_confidence_trend_sync(session)
    stats = _get_prediction_stats_sync(session)

    alerts: list[dict] = []
    overall_status = "GREEN"

    # --- PSI kontrol ---
    psi = input_dist.get("psi", {})
    psi_value = psi.get("total_psi", 0)
    if psi_value > 0.25:
        alerts.append(
            {
                "level": "CRITICAL",
                "message": "Ciddi giris dagilimi kaymasi tespit edildi",
                "metric": "psi",
                "value": psi_value,
            }
        )
        overall_status = "RED"
    elif psi_value > 0.1:
        alerts.append(
            {
                "level": "WARNING",
                "message": "Orta seviye giris dagilimi kaymasi",
                "metric": "psi",
                "value": psi_value,
            }
        )
        if overall_status != "RED":
            overall_status = "YELLOW"

    # --- Confidence kontrol ---
    confidence_alert = confidence.get("alert_level")
    if confidence_alert == "ALARM":
        alerts.append(
            {
                "level": "CRITICAL",
                "message": "Confidence skoru kritik seviyede dusuk (< 0.5)",
                "metric": "confidence_7d_avg",
                "value": confidence.get("moving_avg_7d"),
            }
        )
        overall_status = "RED"
    elif confidence_alert == "WARNING":
        alerts.append(
            {
                "level": "WARNING",
                "message": "Confidence skoru dusuk (< 0.7)",
                "metric": "confidence_7d_avg",
                "value": confidence.get("moving_avg_7d"),
            }
        )
        if overall_status != "RED":
            overall_status = "YELLOW"

    # --- Tahmin sayisi kontrol ---
    total = stats.get("total_predictions", 0)
    if total == 0:
        alerts.append(
            {
                "level": "WARNING",
                "message": "Son 7 gunde hic tahmin yapilmamis",
                "metric": "total_predictions",
                "value": 0,
            }
        )
        if overall_status != "RED":
            overall_status = "YELLOW"

    return {
        "input_distribution": input_dist,
        "confidence_trend": confidence,
        "prediction_stats": stats,
        "overall_status": overall_status,
        "alerts": alerts,
        "generated_at": datetime.now(UTC).isoformat(),
    }


def _check_input_distribution_sync(session: Session, days: int = 7) -> dict:
    """Sync: giris dagilimi kontrol."""
    cutoff = datetime.now(UTC) - timedelta(days=days)

    stmt = select(PredictionLog).where(PredictionLog.created_at >= cutoff)
    result = session.execute(stmt)
    logs = result.scalars().all()

    if not logs:
        return {
            "status": "no_data",
            "days": days,
            "sample_count": 0,
            "psi": {"total_psi": 0, "status": "no_data", "details": {}},
        }

    net_sqms: list[float] = []
    building_ages: list[int] = []
    room_types: list[str] = []

    for log in logs:
        inp = log.input_data or {}
        if "net_sqm" in inp:
            net_sqms.append(float(inp["net_sqm"]))
        if "building_age" in inp:
            building_ages.append(int(inp["building_age"]))

        rc = inp.get("room_count", 0)
        lc = inp.get("living_room_count", 0)
        if rc >= 5:
            room_types.append("5+")
        else:
            room_types.append(f"{rc}+{lc}")

    # Room distribution
    room_dist: dict[str, float] = {}
    if room_types:
        counter = Counter(room_types)
        total = len(room_types)
        room_dist = {k: round(v / total, 4) for k, v in sorted(counter.items())}

    # PSI (referans dagilimla karsilastir)
    psi_result = calculate_psi(room_dist)

    return {
        "status": "ok",
        "days": days,
        "sample_count": len(logs),
        "psi": psi_result,
    }


def _check_confidence_trend_sync(session: Session, days: int = 30) -> dict:
    """Sync: confidence trend."""
    cutoff = datetime.now(UTC) - timedelta(days=days)

    stmt = (
        select(
            func.date(PredictionLog.created_at).label("day"),
            func.avg(PredictionLog.confidence).label("avg_confidence"),
            func.count().label("count"),
        )
        .where(
            PredictionLog.created_at >= cutoff,
            PredictionLog.confidence.isnot(None),
        )
        .group_by(func.date(PredictionLog.created_at))
        .order_by(func.date(PredictionLog.created_at))
    )

    result = session.execute(stmt)
    rows = result.all()

    if not rows:
        return {
            "status": "no_data",
            "days": days,
            "moving_avg_7d": None,
            "alert_level": None,
        }

    confidences = [float(row.avg_confidence) for row in rows]
    last_7 = confidences[-7:] if len(confidences) >= 7 else confidences
    moving_avg_7d = round(sum(last_7) / len(last_7), 4)

    alert_level = None
    if moving_avg_7d < 0.5:
        alert_level = "ALARM"
    elif moving_avg_7d < 0.7:
        alert_level = "WARNING"

    return {
        "status": "ok",
        "days": days,
        "moving_avg_7d": moving_avg_7d,
        "alert_level": alert_level,
    }


def _get_prediction_stats_sync(session: Session, days: int = 7) -> dict:
    """Sync: tahmin istatistikleri."""
    cutoff = datetime.now(UTC) - timedelta(days=days)

    stmt = select(
        func.count().label("total"),
        func.avg(PredictionLog.latency_ms).label("avg_latency_ms"),
        func.avg(PredictionLog.confidence).label("avg_confidence"),
    ).where(PredictionLog.created_at >= cutoff)

    result = session.execute(stmt)
    row = result.one()

    total = row.total or 0
    if total == 0:
        return {"status": "no_data", "days": days, "total_predictions": 0}

    return {
        "status": "ok",
        "days": days,
        "total_predictions": total,
        "avg_latency_ms": (
            round(float(row.avg_latency_ms)) if row.avg_latency_ms else None
        ),
        "avg_confidence": (
            round(float(row.avg_confidence), 4) if row.avg_confidence else None
        ),
    }
