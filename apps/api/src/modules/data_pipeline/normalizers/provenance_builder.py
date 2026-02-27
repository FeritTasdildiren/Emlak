"""
Emlak Teknoloji Platformu - Provenance Builder

Normalizer'lar icin provenance alanlari builder.
ADR-0006 uyumlu data_sources, refresh_status otomatik doldurma.

create_source_entry() fonksiyonunu core/provenance.py'den kullanir,
kendi basina kaynak girisi OLUSTURMAZ — sadece provenance alanlarini bir araya getirir.

Kullanim:
    from src.modules.data_pipeline.normalizers.provenance_builder import build_provenance_fields

    provenance = build_provenance_fields(
        sources=[
            ("TUIK", "2024-W52", 1),
            ("TCMB_EVDS", "2024-12-30", 5),
        ],
    )
    # {"data_sources": [...], "provenance_version": "2024-W52", ...}
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.core.provenance import (
    REFRESH_STATUS_FRESH,
    create_source_entry,
)


def build_provenance_fields(
    sources: list[tuple[str, str, int]],
    status: str = REFRESH_STATUS_FRESH,
    extra_source_kwargs: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """
    Provenance alanlarini olustur.

    Args:
        sources: Kaynak bilgileri listesi.
            Her tuple: (source_name, version, record_count)
            Ornek: [("TUIK", "2024-Q4", 42), ("TCMB_EVDS", "2024-12", 5)]
        status: Refresh durumu (varsayilan: "fresh")
        extra_source_kwargs: Her kaynak icin ek meta veriler.
            Key: source_name, Value: create_source_entry **extra kwargs
            Ornek: {"AFAD": {"data_source": "tucbs_wms", "pga_475": "0.32"}}

    Returns:
        Dict -- Provenance alanlari:
        {
            "data_sources": [
                {"source": "TUIK", "version": "2024-Q4", "fetched_at": "...", "record_count": 42},
                ...
            ],
            "provenance_version": "2024-W52",
            "refresh_status": "fresh",
            "last_refreshed_at": datetime,
            "refresh_error": None
        }
    """
    extra_kwargs = extra_source_kwargs or {}
    now_ts = datetime.now(UTC)

    data_sources = []
    for source_name, version, record_count in sources:
        kwargs = extra_kwargs.get(source_name, {})
        entry = create_source_entry(
            source=source_name,
            version=version,
            record_count=record_count,
            **kwargs,
        )
        data_sources.append(entry)

    # Provenance version: ilk kaynagin versiyonu veya haftalik zaman damgasi
    if sources:
        provenance_version = sources[0][1]
    else:
        provenance_version = now_ts.strftime("%Y-W%W")

    return {
        "data_sources": data_sources,
        "provenance_version": provenance_version,
        "refresh_status": status,
        "last_refreshed_at": now_ts,
        "refresh_error": None,
    }
