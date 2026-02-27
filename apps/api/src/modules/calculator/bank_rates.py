"""Banka konut kredisi faiz oranlari — seed data."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from src.modules.calculator.calculator_schemas import BankRate

# Son guncelleme tarihi (seed)
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


def get_bank_rates() -> list[BankRate]:
    """Mevcut banka faiz oranlarini dondurur.

    Simdilik sabit seed data kullanilir.
    Ileride DB veya dis API'den cekilebilir.

    Returns:
        Banka faiz oranlari listesi.
    """
    return list(DEFAULT_BANK_RATES)
