"""
Emlak Teknoloji Platformu - Provenance Helpers (ADR-0006)

Veri kaynağı izleme, stale data detection, refresh status yönetimi.

Kullanım:
    from src.core.provenance import is_stale, create_source_entry, REFRESH_STATUS_FRESH

    # Stale kontrolü
    if is_stale(area.last_refreshed_at):
        area.refresh_status = REFRESH_STATUS_STALE

    # Yeni kaynak girişi oluştur
    entry = create_source_entry("TUIK", "2024-Q4", record_count=42)
    area.data_sources = [*area.data_sources, entry]
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

# ─── Sabitler ────────────────────────────────────────────────────────

# Stale data eşik değeri (gün). Settings ile override edilebilir.
DEFAULT_STALE_THRESHOLD_DAYS: int = 180  # 6 ay

# Refresh status değerleri — ENUM yerine String (migration kolaylığı)
REFRESH_STATUS_FRESH: str = "fresh"
REFRESH_STATUS_STALE: str = "stale"
REFRESH_STATUS_REFRESHING: str = "refreshing"
REFRESH_STATUS_FAILED: str = "failed"

# Tüm geçerli status değerleri (validasyon için)
VALID_REFRESH_STATUSES: frozenset[str] = frozenset({
    REFRESH_STATUS_FRESH,
    REFRESH_STATUS_STALE,
    REFRESH_STATUS_REFRESHING,
    REFRESH_STATUS_FAILED,
})


# ─── Helper Fonksiyonlar ────────────────────────────────────────────


def is_stale(
    last_refreshed_at: datetime | None,
    threshold_days: int = DEFAULT_STALE_THRESHOLD_DAYS,
) -> bool:
    """
    Verinin güncel olup olmadığını kontrol et.

    Args:
        last_refreshed_at: Son yenileme zamanı (timezone-aware).
                           None ise her zaman stale döner.
        threshold_days: Eşik değer (gün). Default: 180 (6 ay).

    Returns:
        True: Veri stale (eskimiş)
        False: Veri fresh (güncel)

    Examples:
        >>> is_stale(None)
        True
        >>> from datetime import datetime, timezone
        >>> recent = datetime.now(timezone.utc)
        >>> is_stale(recent)
        False
    """
    if last_refreshed_at is None:
        return True

    threshold = datetime.now(UTC) - timedelta(days=threshold_days)
    return last_refreshed_at < threshold


def create_source_entry(
    source: str,
    version: str,
    record_count: int = 0,
    **extra: Any,
) -> dict[str, Any]:
    """
    Provenance data_sources dizisine eklenecek kayıt oluştur.

    Args:
        source: Veri kaynağı adı (ör: "TUIK", "AFAD", "scraping")
        version: Kaynak veri versiyonu (ör: "2024-Q4")
        record_count: Çekilen kayıt sayısı
        **extra: Ek meta veriler (isteğe bağlı)

    Returns:
        Provenance entry dict — data_sources JSONB dizisine eklenmeye hazır.

    Examples:
        >>> entry = create_source_entry("TUIK", "2024-Q4", record_count=42)
        >>> entry["source"]
        'TUIK'
        >>> "fetched_at" in entry
        True
    """
    entry: dict[str, Any] = {
        "source": source,
        "version": version,
        "fetched_at": datetime.now(UTC).isoformat(),
        "record_count": record_count,
    }

    if extra:
        entry.update(extra)

    return entry


def validate_refresh_status(status: str) -> str:
    """
    Refresh status değerini doğrula.

    Args:
        status: Doğrulanacak status değeri.

    Returns:
        Geçerli status string'i.

    Raises:
        ValueError: Geçersiz status değeri.
    """
    if status not in VALID_REFRESH_STATUSES:
        valid = ", ".join(sorted(VALID_REFRESH_STATUSES))
        msg = f"Geçersiz refresh_status: '{status}'. Geçerli değerler: {valid}"
        raise ValueError(msg)
    return status
