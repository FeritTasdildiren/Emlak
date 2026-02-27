"""
Emlak Teknoloji Platformu - Weekly Model Report Beat Task

Haftalik model performans raporu olusturan Celery beat task.

Beat Schedule:
    Her Pazartesi 08:00 (Europe/Istanbul)

Mimari:
    - Sync SQLAlchemy session (Celery worker — psycopg2)
    - WeeklyReportService tum metrikleri toplar
    - structlog ile yapilandirilmis loglama (INFO seviye, tum JSON)
    - Hata durumunda CRITICAL log, retry yok (haftaya tekrar calisir)

Referans: src/tasks/refresh_monitor.py (pattern), TASK-068
"""

from __future__ import annotations

from typing import Any

import structlog

from src.celery_app import celery_app
from src.core.sync_database import get_sync_session
from src.ml.weekly_report import WeeklyReportService
from src.tasks.base import BaseTask

logger = structlog.get_logger("celery.weekly_report")


@celery_app.task(
    base=BaseTask,
    bind=True,
    name="src.tasks.weekly_report.generate_weekly_model_report",
    queue="default",
    soft_time_limit=120,
    time_limit=180,
    autoretry_for=(),
    max_retries=0,
)
def generate_weekly_model_report(self: BaseTask) -> dict[str, Any]:
    """
    Haftalik model performans raporu olustur.

    Beat Schedule: Her Pazartesi 08:00 (Europe/Istanbul)

    Islem akisi:
        1. Sync DB session ac
        2. WeeklyReportService.generate_weekly_report() calistir
        3. Raporu structlog ile logla (INFO seviye)
        4. Raporu sonuc olarak dondur (ileride email gondermek icin)

    Hata durumunda:
        - structlog CRITICAL log
        - Retry yok — haftaya tekrar calisir

    Returns:
        Haftalik rapor dict'i.
    """
    self.log.info("weekly_report_started")

    try:
        with get_sync_session() as session:
            service = WeeklyReportService(session)
            report = service.generate_weekly_report()

        # ── Raporu logla ──
        self.log.info(
            "weekly_report_completed",
            report_date=report["report_date"],
            model_version=report["model_version"],
            total_predictions=report["summary"]["total_predictions"],
            avg_confidence=report["summary"]["avg_confidence"],
            avg_latency_ms=report["summary"]["avg_latency_ms"],
            unique_users=report["summary"]["unique_users"],
            unique_districts=report["summary"]["unique_districts"],
            alert_count=len(report["alerts"]),
            trend=report["confidence_trend"]["trend"],
        )

        # Alert'ler varsa ayrica logla
        for alert in report["alerts"]:
            if alert["severity"] == "WARNING":
                self.log.warning(
                    "weekly_report_alert",
                    severity=alert["severity"],
                    message=alert["message"],
                )
            else:
                self.log.info(
                    "weekly_report_alert",
                    severity=alert["severity"],
                    message=alert["message"],
                )

        return report

    except Exception:
        self.log.critical(
            "weekly_report_failed",
            exc_info=True,
        )
        raise
