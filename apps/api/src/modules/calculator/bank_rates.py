"""Banka konut kredisi faiz oranlari — DB + fallback seed data.

Birincil kaynak: bank_rates DB tablosu (migration 024 ile olusturulur).
Fallback: DEFAULT_BANK_RATES listesi (DB erisilemezse graceful degradation).

Referans: TASK-193
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from src.models.bank_rate import BankRate as BankRateModel
from src.modules.calculator.calculator_schemas import BankRate

logger = structlog.get_logger()

# Son guncelleme tarihi (seed fallback)
_LAST_UPDATED = datetime(2025, 2, 1, tzinfo=UTC)

DEFAULT_BANK_RATES: list[BankRate] = [
    BankRate(
        bank_name="Ziraat Bankası",
        annual_rate=Decimal("3.09"),
        min_term=12,
        max_term=120,
        min_amount=Decimal("100000.00"),
        max_amount=Decimal("10000000.00"),
        updated_at=_LAST_UPDATED,
    ),
    BankRate(
        bank_name="Halkbank",
        annual_rate=Decimal("3.19"),
        min_term=12,
        max_term=120,
        min_amount=Decimal("100000.00"),
        max_amount=Decimal("10000000.00"),
        updated_at=_LAST_UPDATED,
    ),
    BankRate(
        bank_name="Vakıfbank",
        annual_rate=Decimal("3.29"),
        min_term=12,
        max_term=120,
        min_amount=Decimal("100000.00"),
        max_amount=Decimal("10000000.00"),
        updated_at=_LAST_UPDATED,
    ),
    BankRate(
        bank_name="İş Bankası",
        annual_rate=Decimal("3.39"),
        min_term=12,
        max_term=96,
        min_amount=Decimal("150000.00"),
        max_amount=Decimal("8000000.00"),
        updated_at=_LAST_UPDATED,
    ),
    BankRate(
        bank_name="Garanti BBVA",
        annual_rate=Decimal("3.49"),
        min_term=12,
        max_term=120,
        min_amount=Decimal("100000.00"),
        max_amount=Decimal("10000000.00"),
        updated_at=_LAST_UPDATED,
    ),
    BankRate(
        bank_name="Yapı Kredi",
        annual_rate=Decimal("3.44"),
        min_term=12,
        max_term=120,
        min_amount=Decimal("100000.00"),
        max_amount=Decimal("10000000.00"),
        updated_at=_LAST_UPDATED,
    ),
]


async def get_bank_rates_from_db(session: AsyncSession) -> list[BankRate]:
    """DB'den aktif banka faiz oranlarini getirir.

    Async session ile calisir (FastAPI endpoint'leri icin).
    Hata durumunda DEFAULT_BANK_RATES'e fallback yapar.

    Args:
        session: SQLAlchemy async session.

    Returns:
        Aktif banka faiz oranlari listesi (faiz oranina gore artan sirali).
    """
    try:
        stmt = (
            select(BankRateModel)
            .where(BankRateModel.is_active.is_(True))
            .order_by(BankRateModel.annual_rate.asc())
        )
        result = await session.execute(stmt)
        rows = result.scalars().all()

        if not rows:
            logger.warning("bank_rates_db_empty", fallback="DEFAULT_BANK_RATES")
            return list(DEFAULT_BANK_RATES)

        return [BankRate.model_validate(row) for row in rows]
    except Exception:
        logger.exception("bank_rates_db_error", fallback="DEFAULT_BANK_RATES")
        return list(DEFAULT_BANK_RATES)


def get_bank_rates() -> list[BankRate]:
    """Mevcut banka faiz oranlarini dondurur (fallback — sync).

    DB erisimi olmayan context'lerde (test, Celery fallback vb.)
    DEFAULT_BANK_RATES seed data'sini dondurur.

    Returns:
        Banka faiz oranlari listesi.
    """
    return list(DEFAULT_BANK_RATES)
