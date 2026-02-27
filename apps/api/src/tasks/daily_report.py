"""
Emlak Teknoloji Platformu - Daily Office Report Beat Task

Gunluk ofis raporu olusturup Telegram'a gonderen Celery beat task.

Beat Schedule:
    Her gun 20:00 TST (17:00 UTC) — crontab(hour=17, minute=0)
    Queue: notifications

Mimari:
    - DB erisimi: Sync psycopg2 (get_sync_session)
    - Telegram gonderimi: asyncio.run() ile tek seferlik async cagri
      (aiogram async API — Celery prefork worker'da event loop yok)
    - TelegramAdapter: task basina olusturulur/kapatilir (HTTP session leak yok)
    - Hata izolasyonu: Bir ofis basarisiz olursa diger ofisler etkilenmez
    - Retry yok — ertesi gun otomatik tekrar calisir

Referans: TASK-136, drift_check.py (sync DB), matches/tasks.py (Telegram pattern)
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

import structlog

from src.celery_app import celery_app
from src.config import settings
from src.core.sync_database import get_sync_session
from src.models.user import User
from src.modules.messaging.schemas import MessageContent
from src.modules.reporting.daily_report_service import (
    DailyReportData,
    DailyReportService,
    format_daily_report_telegram,
)
from src.tasks.base import BaseTask

logger = structlog.get_logger("celery.daily_report")


# ================================================================
# Telegram Gonderim Helper (async — matches/tasks.py pattern'i)
# ================================================================


async def _send_telegram_report(chat_id: str, text: str) -> bool:
    """
    Tek bir Telegram mesaji gonderir.

    Adapter task basina olusturulur ve kapatilir — HTTP session leak onlenir.

    Returns:
        True → basarili gonderim, False → hata.
    """
    from src.modules.messaging.adapters.telegram import TelegramAdapter

    adapter = TelegramAdapter(bot_token=settings.TELEGRAM_BOT_TOKEN)
    try:
        content = MessageContent(text=text)
        result = await adapter.send(recipient=chat_id, content=content)
        return result.success
    finally:
        with contextlib.suppress(Exception):
            await adapter.close()


# ================================================================
# Ofis Rapor Gondericisi (sync — per-office isolation)
# ================================================================


def _send_report_for_office(
    report: DailyReportData,
    admin_chat_ids: list[str],
    task_log: structlog.stdlib.BoundLogger,
) -> dict[str, Any]:
    """
    Tek ofis icin raporu Telegram'a gonder.

    Args:
        report: Ofis rapor verisi.
        admin_chat_ids: Ofis yoneticilerinin telegram_chat_id listesi.
        task_log: Structlog bound logger.

    Returns:
        dict: sent_count, error (varsa).
    """
    telegram_text = format_daily_report_telegram(report)
    sent_count = 0

    for chat_id in admin_chat_ids:
        try:
            success = asyncio.run(_send_telegram_report(chat_id, telegram_text))
            if success:
                sent_count += 1
            else:
                task_log.warning(
                    "daily_report_telegram_delivery_failed",
                    office_id=report.office_id,
                    chat_id=chat_id,
                )
        except Exception:
            task_log.warning(
                "daily_report_telegram_send_error",
                office_id=report.office_id,
                chat_id=chat_id,
                exc_info=True,
            )

    return {"sent_count": sent_count}


# ================================================================
# Celery Beat Task
# ================================================================


@celery_app.task(
    bind=True,
    base=BaseTask,
    queue="notifications",
    name="src.tasks.daily_report.send_daily_office_reports",
    soft_time_limit=120,
    time_limit=180,
    # Monitoring/report task — retry yok, ertesi gun tekrar calisir
    autoretry_for=(),
    max_retries=0,
)
def send_daily_office_reports(self: BaseTask) -> dict[str, Any]:
    """
    Gunluk ofis raporlarini olustur ve Telegram'a gonder.

    Beat Schedule: Her gun 20:00 TST (17:00 UTC)
    Queue: notifications

    Islem akisi:
        1. Tum aktif ofisler icin rapor verilerini topla (sync DB)
        2. Her ofis icin yonetici(lerin) telegram_chat_id'lerini bul
        3. Telegram'a gonder (asyncio.run — aiogram)
        4. Sonuclari logla

    Hata izolasyonu:
        - Bir ofis fail ederse digerleri etkilenmez (try/except per office)
        - Telegram gonderim hatasi → logla, crash etme

    Returns:
        dict: Rapor ozeti (office_count, total_sent, failed_offices).
    """
    self.log.info("daily_report_started")

    # ── Telegram token kontrolu ──
    if not settings.TELEGRAM_BOT_TOKEN:
        self.log.warning("daily_report_skipped_no_telegram_token")
        return {"status": "skipped", "reason": "TELEGRAM_BOT_TOKEN not configured"}

    total_sent = 0
    failed_offices: list[str] = []
    office_count = 0

    try:
        with get_sync_session() as session:
            # ── 1. Rapor verilerini topla ──
            service = DailyReportService(session)
            reports = service.generate_all_reports()
            office_count = len(reports)

            if not reports:
                self.log.info("daily_report_no_active_offices")
                return {"status": "ok", "office_count": 0, "total_sent": 0}

            # ── 2. Her ofis icin yoneticileri bul ve gonder ──
            for report in reports:
                try:
                    # Ofis yoneticilerinin telegram_chat_id'lerini bul
                    admin_chat_ids = _get_office_admin_chat_ids(
                        session, report.office_id,
                    )

                    if not admin_chat_ids:
                        self.log.info(
                            "daily_report_no_admin_chat_id",
                            office_id=report.office_id,
                            office_name=report.office_name,
                        )
                        continue

                    # Telegram'a gonder
                    result = _send_report_for_office(
                        report=report,
                        admin_chat_ids=admin_chat_ids,
                        task_log=self.log,
                    )
                    total_sent += result["sent_count"]

                    self.log.info(
                        "daily_report_office_done",
                        office_id=report.office_id,
                        office_name=report.office_name,
                        sent_count=result["sent_count"],
                        total_properties=report.total_properties,
                        new_properties=report.new_properties_today,
                        valuations_today=report.valuations_today,
                        matches_today=report.matches_today,
                    )

                except Exception:
                    # ── HATA IZOLASYONU: Bir ofis fail ederse digerleri devam eder ──
                    failed_offices.append(report.office_id)
                    self.log.exception(
                        "daily_report_office_error",
                        office_id=report.office_id,
                        office_name=report.office_name,
                    )

    except Exception:
        self.log.critical("daily_report_db_error", exc_info=True)
        return {
            "status": "error",
            "error": "Veritabani hatasi",
            "office_count": office_count,
            "total_sent": total_sent,
        }

    # ── Sonuc ──
    status = "ok" if not failed_offices else "partial"

    self.log.info(
        "daily_report_completed",
        status=status,
        office_count=office_count,
        total_sent=total_sent,
        failed_count=len(failed_offices),
    )

    return {
        "status": status,
        "office_count": office_count,
        "total_sent": total_sent,
        "failed_offices": failed_offices,
    }


# ================================================================
# Helper: Ofis Yoneticisi Chat ID'leri
# ================================================================


def _get_office_admin_chat_ids(session: object, office_id: str) -> list[str]:
    """
    Ofis yoneticilerinin Telegram chat_id'lerini getir.

    Roller: office_admin, office_owner
    Filtre: is_active=True, telegram_chat_id IS NOT NULL

    Returns:
        Gecerli telegram_chat_id listesi.
    """
    from sqlalchemy import select

    stmt = (
        select(User.telegram_chat_id)
        .where(
            User.office_id == office_id,
            User.role.in_(["office_admin", "office_owner"]),
            User.is_active.is_(True),
            User.telegram_chat_id.isnot(None),
        )
    )
    result = session.execute(stmt)  # type: ignore[union-attr]
    return [row[0] for row in result.all()]
