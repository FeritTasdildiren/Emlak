"""
Emlak Teknoloji Platformu - Plan Policy Engine

Abonelik planlarına göre kanal yeteneklerini tek noktadan yönetir (policy pattern).
Tüm plan kısıtlama kontrolleri bu modül üzerinden yapılır.

Plan seviyeleri:
    - Starter : Telegram Bot + WhatsApp Click-to-Chat
    - Pro     : Telegram Bot + WhatsApp Click-to-Chat
    - Elite   : Telegram Bot + WhatsApp Click-to-Chat + WhatsApp Cloud API

Kullanım:
    from src.core.plan_policy import get_capabilities, PlanType

    caps = get_capabilities("elite")
    if caps["whatsapp_cloud_api"]:
        # WhatsApp Cloud API entegrasyonunu etkinleştir
        ...
"""

from enum import StrEnum
from typing import TypedDict


class PlanType(StrEnum):
    """Abonelik plan tipleri."""

    STARTER = "starter"
    PRO = "pro"
    ELITE = "elite"


class ChannelCapability(TypedDict):
    """
    Plan bazlı kanal yetenekleri.

    Her alan bir iletişim kanalının aktif olup olmadığını belirtir.
    """

    telegram_bot: bool
    whatsapp_click_to_chat: bool
    whatsapp_cloud_api: bool


# ================================================================
# Merkezi plan yetenek tanımları
# ================================================================
# Yeni bir kanal veya plan eklendiğinde SADECE burayı güncelleyin.
# Uygulama genelinde get_capabilities() kullanılır.
PLAN_CAPABILITIES: dict[PlanType, ChannelCapability] = {
    PlanType.STARTER: ChannelCapability(
        telegram_bot=True,
        whatsapp_click_to_chat=True,
        whatsapp_cloud_api=False,
    ),
    PlanType.PRO: ChannelCapability(
        telegram_bot=True,
        whatsapp_click_to_chat=True,
        whatsapp_cloud_api=False,
    ),
    PlanType.ELITE: ChannelCapability(
        telegram_bot=True,
        whatsapp_click_to_chat=True,
        whatsapp_cloud_api=True,
    ),
}


# ================================================================
# Aylik degerleme kota limitleri (plan bazli)
# ================================================================
# Elite plan unlimited (-1) olarak tanimlanir.
# Yeni bir plan eklendiginde SADECE burasini guncelleyin.
PLAN_VALUATION_QUOTAS: dict[PlanType, int] = {
    PlanType.STARTER: 50,
    PlanType.PRO: 500,
    PlanType.ELITE: -1,  # Sinirsiz
}


def get_valuation_quota(plan_type: str) -> int:
    """
    Plan tipine gore aylik degerleme kotasini dondurur.

    Args:
        plan_type: Plan tipi string'i (starter, pro, elite).

    Returns:
        int — aylik kota limiti. -1 = sinirsiz.

    Raises:
        ValueError: Gecersiz plan tipi verildiginde.
    """
    try:
        plan = PlanType(plan_type.lower())
    except ValueError as exc:
        valid = [p.value for p in PlanType]
        raise ValueError(f"Gecersiz plan tipi: '{plan_type}'. Gecerli degerler: {valid}") from exc

    return PLAN_VALUATION_QUOTAS[plan]


def is_unlimited_plan(plan_type: str) -> bool:
    """Elite plan gibi sinirsiz kota olan planlar icin True doner."""
    return get_valuation_quota(plan_type) == -1


# ================================================================
# Ilan kota limitleri (plan bazli)
# ================================================================
# -1 = sinirsiz. Yeni bir plan eklendiginde SADECE burasini guncelleyin.
PLAN_LISTING_QUOTAS: dict[PlanType, int] = {
    PlanType.STARTER: 20,
    PlanType.PRO: 100,
    PlanType.ELITE: -1,  # Sinirsiz
}


def get_listing_quota(plan_type: str) -> int:
    """
    Plan tipine gore aylik ilan kotasini dondurur.

    Args:
        plan_type: Plan tipi string'i (starter, pro, elite).

    Returns:
        int — aylik ilan kota limiti. -1 = sinirsiz.

    Raises:
        ValueError: Gecersiz plan tipi verildiginde.
    """
    try:
        plan = PlanType(plan_type.lower())
    except ValueError as exc:
        valid = [p.value for p in PlanType]
        raise ValueError(f"Gecersiz plan tipi: '{plan_type}'. Gecerli degerler: {valid}") from exc

    return PLAN_LISTING_QUOTAS[plan]


# ================================================================
# Sahneleme (staging) kota limitleri (plan bazli)
# ================================================================
PLAN_STAGING_QUOTAS: dict[PlanType, int] = {
    PlanType.STARTER: 10,
    PlanType.PRO: 50,
    PlanType.ELITE: 200,
}


def get_staging_quota(plan_type: str) -> int:
    """
    Plan tipine gore aylik sahneleme kotasini dondurur.

    Args:
        plan_type: Plan tipi string'i (starter, pro, elite).

    Returns:
        int — aylik sahneleme kota limiti.

    Raises:
        ValueError: Gecersiz plan tipi verildiginde.
    """
    try:
        plan = PlanType(plan_type.lower())
    except ValueError as exc:
        valid = [p.value for p in PlanType]
        raise ValueError(f"Gecersiz plan tipi: '{plan_type}'. Gecerli degerler: {valid}") from exc

    return PLAN_STAGING_QUOTAS[plan]


# ================================================================
# Fotograf kota limitleri (plan bazli)
# ================================================================
PLAN_PHOTO_QUOTAS: dict[PlanType, int] = {
    PlanType.STARTER: 100,
    PlanType.PRO: 500,
    PlanType.ELITE: -1,  # Sinirsiz
}


def get_photo_quota(plan_type: str) -> int:
    """
    Plan tipine gore aylik fotograf kotasini dondurur.

    Args:
        plan_type: Plan tipi string'i (starter, pro, elite).

    Returns:
        int — aylik fotograf kota limiti. -1 = sinirsiz.

    Raises:
        ValueError: Gecersiz plan tipi verildiginde.
    """
    try:
        plan = PlanType(plan_type.lower())
    except ValueError as exc:
        valid = [p.value for p in PlanType]
        raise ValueError(f"Gecersiz plan tipi: '{plan_type}'. Gecerli degerler: {valid}") from exc

    return PLAN_PHOTO_QUOTAS[plan]


def is_unlimited_quota(plan_type: str, quota_type: str) -> bool:
    """
    Belirtilen plan ve kota tipi icin sinirsiz olup olmadigini dondurur.

    Args:
        plan_type: Plan tipi string'i (starter, pro, elite).
        quota_type: Kota tipi string'i (valuation, listing, staging, photo).

    Returns:
        True — kota sinirsiz (-1).
    """
    _quota_getter_map: dict[str, object] = {
        "valuation": get_valuation_quota,
        "listing": get_listing_quota,
        "staging": get_staging_quota,
        "photo": get_photo_quota,
    }
    getter = _quota_getter_map.get(quota_type)
    if getter is None:
        return False
    return getter(plan_type) == -1


# ================================================================
# Musteri kota limitleri (plan bazli)
# ================================================================
# Elite plan unlimited (-1) olarak tanimlanir.
# Yeni bir plan eklendiginde SADECE burasini guncelleyin.
PLAN_CUSTOMER_QUOTAS: dict[PlanType, int] = {
    PlanType.STARTER: 50,
    PlanType.PRO: 500,
    PlanType.ELITE: -1,  # Sinirsiz
}


def get_customer_quota(plan_type: str) -> int:
    """
    Plan tipine gore musteri kotasini dondurur.

    Args:
        plan_type: Plan tipi string'i (starter, pro, elite).

    Returns:
        int — musteri kota limiti. -1 = sinirsiz.

    Raises:
        ValueError: Gecersiz plan tipi verildiginde.
    """
    try:
        plan = PlanType(plan_type.lower())
    except ValueError as exc:
        valid = [p.value for p in PlanType]
        raise ValueError(f"Gecersiz plan tipi: '{plan_type}'. Gecerli degerler: {valid}") from exc

    return PLAN_CUSTOMER_QUOTAS[plan]


def get_capabilities(plan_type: str) -> ChannelCapability:
    """
    Plan tipine göre kanal yeteneklerini döndürür.

    Args:
        plan_type: Plan tipi string'i (starter, pro, elite).
                   Subscription tablosundaki plan_type alanından gelir.

    Returns:
        ChannelCapability — kanal bazlı bool yetenekler.

    Raises:
        ValueError: Geçersiz plan tipi verildiğinde.

    Örnek:
        >>> get_capabilities("starter")
        {'telegram_bot': True, 'whatsapp_click_to_chat': True, 'whatsapp_cloud_api': False}
    """
    try:
        plan = PlanType(plan_type.lower())
    except ValueError as exc:
        valid = [p.value for p in PlanType]
        raise ValueError(f"Geçersiz plan tipi: '{plan_type}'. Geçerli değerler: {valid}") from exc

    return PLAN_CAPABILITIES[plan]
