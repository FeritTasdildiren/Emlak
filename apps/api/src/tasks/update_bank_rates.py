"""
Emlak Teknoloji Platformu - Bank Rates Freshness Check Task

Celery Beat tarafindan gunluk olarak calistirilir.
Banka faiz oranlarinin ne kadar eski oldugunu kontrol eder.

Schedule: Her gun 09:00 (Europe/Istanbul)
Queue: default

Mimari Karar:
    Sync psycopg2 kullanir (Celery worker'da async KULLANILMAZ).
    7 gun uzerinde eski oranlar icin WARNING log uretir.
    Ileride Telegram alert veya TCMB API proxy eklenebilir.

Referans: TASK-193
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import func, select

from src.celery_app import celery_app
from src.core.sync_database import get_sync_session
from src.models.bank_rate import BankRate as BankRateModel
from src.tasks.base import BaseTask

# Esik: Bu gun sayisindan eski oranlar "stale" kabul edilir
_STALE_THRESHOLD_DAYS = 7


@celery_app.task(
    bind=True,
    base=BaseTask,
    queue="default",
    name="src.tasks.update_bank_rates.check_bank_rates_freshness",
    # Monitoring task — retry yapmasin, bir sonraki beat'te tekrar calisir
    autoretry_for=(),
    max_retries=0,
)
def check_bank_rates_freshness(self: BaseTask) -> dict[str, Any]:
    """Gunluk banka faiz orani tazelik kontrolu.

    Celery Beat tarafindan her gun 09:00'da cagirilir.
    En eski aktif oranin kac gun once guncelledigini kontrol eder.
    7 gun uzerinde eski oranlar icin WARNING log uretir.

    Returns:
        dict: Kontrol raporu ozeti.
    """
    self.log.info("bank_rates_freshness_check_started")

    try:
        with get_sync_session() as session:
            # En eski aktif oranin updated_at degerini bul
            oldest_update = session.execute(
                select(func.min(BankRateModel.updated_at)).where(
                    BankRateModel.is_active.is_(True)
                )
            ).scalar()

            # Aktif oran sayisi
            active_count = session.execute(
                select(func.count()).where(BankRateModel.is_active.is_(True))
            ).scalar()

    except Exception:
        self.log.exception("bank_rates_freshness_db_error")
        return {
            "status": "error",
            "error": "Veritabani hatasi",
            "checked_at": datetime.now(UTC).isoformat(),
        }

    if oldest_update is None:
        self.log.warning("bank_rates_no_active_rates")
        return {
            "status": "no_data",
            "active_count": 0,
            "checked_at": datetime.now(UTC).isoformat(),
        }

    days_old = (datetime.now(UTC) - oldest_update).days

    if days_old > _STALE_THRESHOLD_DAYS:
        self.log.warning(
            "bank_rates_stale",
            oldest_update=oldest_update.isoformat(),
            days_old=days_old,
            active_count=active_count,
            threshold_days=_STALE_THRESHOLD_DAYS,
        )
        status = "stale"
    else:
        self.log.info(
            "bank_rates_fresh",
            oldest_update=oldest_update.isoformat(),
            days_old=days_old,
            active_count=active_count,
        )
        status = "fresh"

    return {
        "status": status,
        "oldest_update": oldest_update.isoformat(),
        "days_old": days_old,
        "active_count": active_count,
        "threshold_days": _STALE_THRESHOLD_DAYS,
        "checked_at": datetime.now(UTC).isoformat(),
    }
