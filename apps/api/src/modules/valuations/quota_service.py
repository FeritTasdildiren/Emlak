"""
Emlak Teknoloji Platformu - Quota Service

Aylık kota yönetimi: değerleme, ilan, sahneleme ve fotoğraf.
Her işlem öncesinde kota kontrolü yapılır, sonrasında sayaç artırılır.
Kota aşılırsa credit_balance üzerinden ekstra kredi kullanılabilir.

Kullanım:
    from src.modules.valuations.quota_service import (
        QuotaType, check_quota, increment_quota,
        check_credit, use_credit,
    )

    allowed, used, limit = await check_quota(db, office_id, plan, QuotaType.VALUATION)
    if not allowed:
        has_credit = await check_credit(db, office_id, plan, QuotaType.VALUATION)
        if has_credit:
            await use_credit(db, office_id, plan, QuotaType.VALUATION)
        else:
            raise HTTPException(429, "Aylık kota aşıldı")
    # ... işlemi yap ...
    await increment_quota(db, office_id, plan, QuotaType.VALUATION)
"""

from __future__ import annotations

import calendar
from datetime import date
from enum import StrEnum
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

from src.core.plan_policy import (
    get_listing_quota,
    get_photo_quota,
    get_staging_quota,
    get_valuation_quota,
    is_unlimited_quota,
)
from src.modules.valuations.models.usage_quota import UsageQuota

logger = structlog.get_logger()


# ================================================================
# Kota Tipleri
# ================================================================
class QuotaType(StrEnum):
    """Desteklenen kota tipleri."""

    VALUATION = "valuation"
    LISTING = "listing"
    STAGING = "staging"
    PHOTO = "photo"


# ---------- Kota tipi → model alanı eşlemesi ----------
_USED_FIELD_MAP: dict[QuotaType, str] = {
    QuotaType.VALUATION: "valuations_used",
    QuotaType.LISTING: "listings_used",
    QuotaType.STAGING: "staging_used",
    QuotaType.PHOTO: "photos_used",
}

# ---------- Kota tipi → plan_policy fonksiyonu eşlemesi ----------
_QUOTA_GETTER_MAP = {
    QuotaType.VALUATION: get_valuation_quota,
    QuotaType.LISTING: get_listing_quota,
    QuotaType.STAGING: get_staging_quota,
    QuotaType.PHOTO: get_photo_quota,
}


def _current_period() -> tuple[date, date]:
    """Mevcut ayın başlangıç ve bitiş tarihlerini döndürür."""
    today = date.today()
    first_day = today.replace(day=1)
    last_day_num = calendar.monthrange(today.year, today.month)[1]
    last_day = today.replace(day=last_day_num)
    return first_day, last_day


def _get_limit_for_type(plan: str, quota_type: QuotaType) -> int:
    """Plan ve kota tipine göre limiti döndürür."""
    getter = _QUOTA_GETTER_MAP[quota_type]
    return getter(plan)


async def get_or_create_quota(
    db: AsyncSession,
    office_id: uuid.UUID,
    plan: str,
) -> UsageQuota:
    """
    Mevcut ay için kota kaydını getirir, yoksa oluşturur.

    Args:
        db: Async veritabanı oturumu.
        office_id: Ofis UUID'si.
        plan: Abonelik plan tipi (starter, pro, elite).

    Returns:
        UsageQuota — mevcut veya yeni oluşturulan kota kaydı.
    """
    period_start, period_end = _current_period()

    stmt = select(UsageQuota).where(
        UsageQuota.office_id == office_id,
        UsageQuota.period_start == period_start,
    )
    result = await db.execute(stmt)
    quota = result.scalar_one_or_none()

    if quota is not None:
        return quota

    # Yeni ay — kota kaydı oluştur
    limit = get_valuation_quota(plan)
    quota = UsageQuota(
        office_id=office_id,
        period_start=period_start,
        period_end=period_end,
        valuations_used=0,
        valuations_limit=limit,
    )
    db.add(quota)
    await db.flush()

    logger.info(
        "usage_quota.created",
        office_id=str(office_id),
        period=str(period_start),
        limit=limit,
    )
    return quota


async def check_quota(
    db: AsyncSession,
    office_id: uuid.UUID,
    plan: str,
    quota_type: QuotaType = QuotaType.VALUATION,
) -> tuple[bool, int, int]:
    """
    Belirtilen kota tipinin durumunu kontrol eder.

    Args:
        db: Async veritabanı oturumu.
        office_id: Ofis UUID'si.
        plan: Abonelik plan tipi.
        quota_type: Kontrol edilecek kota tipi.

    Returns:
        (is_allowed, used, limit) tuple'ı.
        is_allowed: Yeni işlem yapılabilir mi?
        used: Bu ay kullanılan sayı.
        limit: Aylık limit (-1 = sınırsız).
    """
    quota = await get_or_create_quota(db, office_id, plan)
    limit = _get_limit_for_type(plan, quota_type)
    unlimited = is_unlimited_quota(plan, quota_type.value)

    used_field = _USED_FIELD_MAP[quota_type]
    used = getattr(quota, used_field)

    is_allowed = unlimited or used < limit
    return is_allowed, used, limit


async def increment_quota(
    db: AsyncSession,
    office_id: uuid.UUID,
    plan: str,
    quota_type: QuotaType = QuotaType.VALUATION,
) -> UsageQuota:
    """
    Belirtilen kota tipinin sayacını 1 artırır.

    İşlem başarıyla tamamlandıktan sonra çağrılmalıdır.

    Args:
        db: Async veritabanı oturumu.
        office_id: Ofis UUID'si.
        plan: Abonelik plan tipi.
        quota_type: Artırılacak kota tipi.

    Returns:
        UsageQuota — güncellenmiş kota kaydı.
    """
    quota = await get_or_create_quota(db, office_id, plan)
    used_field = _USED_FIELD_MAP[quota_type]
    current_val = getattr(quota, used_field)
    setattr(quota, used_field, current_val + 1)
    await db.flush()

    logger.info(
        "usage_quota.incremented",
        office_id=str(office_id),
        quota_type=quota_type.value,
        used=current_val + 1,
        limit=_get_limit_for_type(plan, quota_type),
    )
    return quota


async def check_credit(
    db: AsyncSession,
    office_id: uuid.UUID,
    plan: str,
    quota_type: QuotaType,
) -> bool:
    """
    Kota aşıldığında credit_balance kontrolü yapar.

    Kota doluysa ve credit_balance > 0 ise True döner.
    Kota dolmamışsa da True döner (kredit kullanmaya gerek yok).

    Args:
        db: Async veritabanı oturumu.
        office_id: Ofis UUID'si.
        plan: Abonelik plan tipi.
        quota_type: Kontrol edilecek kota tipi.

    Returns:
        True — işlem yapılabilir (kota müsait veya kredi var).
        False — hem kota dolu hem kredi yok.
    """
    is_allowed, _used, _limit = await check_quota(db, office_id, plan, quota_type)
    if is_allowed:
        return True

    # Kota dolmuş — credit_balance kontrol et
    quota = await get_or_create_quota(db, office_id, plan)
    return quota.credit_balance > 0


async def use_credit(
    db: AsyncSession,
    office_id: uuid.UUID,
    plan: str,
    quota_type: QuotaType,
) -> UsageQuota:
    """
    Credit balance'dan 1 kredi düşer ve ilgili sayacı artırır.

    Kota aşıldığında ve credit_balance > 0 olduğunda çağrılır.

    Args:
        db: Async veritabanı oturumu.
        office_id: Ofis UUID'si.
        plan: Abonelik plan tipi.
        quota_type: Kredi kullanılacak kota tipi.

    Returns:
        UsageQuota — güncellenmiş kota kaydı.

    Raises:
        ValueError: credit_balance 0 veya negatifse.
    """
    quota = await get_or_create_quota(db, office_id, plan)

    if quota.credit_balance <= 0:
        raise ValueError("Yetersiz kredi bakiyesi.")

    # Kredi düş
    quota.credit_balance -= 1

    # İlgili sayacı artır
    used_field = _USED_FIELD_MAP[quota_type]
    current_val = getattr(quota, used_field)
    setattr(quota, used_field, current_val + 1)

    await db.flush()

    logger.info(
        "usage_quota.credit_used",
        office_id=str(office_id),
        quota_type=quota_type.value,
        remaining_credits=quota.credit_balance,
    )
    return quota


async def add_credits(
    db: AsyncSession,
    office_id: uuid.UUID,
    plan: str,
    amount: int,
) -> UsageQuota:
    """
    Credit balance'a kredi ekler.

    Args:
        db: Async veritabanı oturumu.
        office_id: Ofis UUID'si.
        plan: Abonelik plan tipi.
        amount: Eklenecek kredi miktarı.

    Returns:
        UsageQuota — güncellenmiş kota kaydı.

    Raises:
        ValueError: amount <= 0 ise.
    """
    if amount <= 0:
        raise ValueError("Kredi miktari 0'dan buyuk olmalidir.")

    quota = await get_or_create_quota(db, office_id, plan)
    quota.credit_balance += amount
    await db.flush()

    logger.info(
        "usage_quota.credits_added",
        office_id=str(office_id),
        amount=amount,
        new_balance=quota.credit_balance,
    )
    return quota


async def get_credit_balance(
    db: AsyncSession,
    office_id: uuid.UUID,
    plan: str,
) -> int:
    """
    Mevcut kredi bakiyesini döndürür.

    Args:
        db: Async veritabanı oturumu.
        office_id: Ofis UUID'si.
        plan: Abonelik plan tipi.

    Returns:
        Mevcut credit_balance değeri.
    """
    quota = await get_or_create_quota(db, office_id, plan)
    return quota.credit_balance
