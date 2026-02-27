"""
Emlak Teknoloji Platformu - Price History Normalizer

TUIK konut satis verilerini PriceHistory entity'lerine normalize eder.
Her aya ait satis verisi ayri bir PriceHistory kaydina donusturulur.

Kullanim:
    from src.modules.data_pipeline.normalizers import normalize_price_history

    records = normalize_price_history(
        city="Istanbul",
        district="Kadikoy",
        sales_data=sales,
        hpi_data=hpi_list,
    )
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any

import structlog

from src.modules.data_pipeline.schemas.api_responses import (
    HousingPriceIndexData,
    HousingSaleData,
)

logger = structlog.get_logger("data_pipeline.normalizers.price_history")


def _safe_decimal(value: Any, default: str = "0.00") -> Decimal:
    """float/int/str -> guvenli Decimal. float -> str -> Decimal zinciri."""
    if value is None:
        return Decimal(default)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def normalize_price_history(
    city: str,
    district: str,
    sales_data: list[HousingSaleData],
    hpi_data: list[HousingPriceIndexData] | None = None,
    neighborhood: str | None = None,
) -> list[dict[str, Any]]:
    """
    Satis verilerini aylik PriceHistory kayitlarina donustur.

    Her HousingSaleData bir aylik PriceHistory kaydina eslestirilir.
    HPI verisi mevcutsa tahmini m2 fiyati hesaplanir.

    Args:
        city: Il adi
        district: Ilce adi
        sales_data: TUIK konut satis verileri
        hpi_data: TCMB konut fiyat endeksi verileri (opsiyonel)
        neighborhood: Mahalle adi (opsiyonel)

    Returns:
        List[Dict] -- Her ay icin bir kayit.
        Ornek: [{
            "area_type": "district",
            "area_name": "Kadikoy",
            "city": "Istanbul",
            "district": "Kadikoy",
            "date": date(2024, 12, 1),
            "transaction_count": 1234,
            "avg_price_sqm": Decimal("52300.00"),
            "source": "TUIK",
            "provenance_version": "TUIK-2024-12",
        }]
    """
    if not sales_data:
        return []

    # -- HPI lookup: year-month -> index_value --
    hpi_lookup: dict[str, float] = {}
    if hpi_data:
        for hpi in hpi_data:
            key = hpi.date.strftime("%Y-%m")
            hpi_lookup[key] = hpi.index_value

    # -- Area type belirleme --
    if neighborhood:
        area_type = "neighborhood"
        area_name = neighborhood
    elif district:
        area_type = "district"
        area_name = district
    else:
        area_type = "city"
        area_name = city

    records: list[dict[str, Any]] = []

    for sale in sales_data:
        # Ay bilgisi 0 ise yillik toplam — atla (aylik kayit isteniyor)
        if sale.month == 0:
            continue

        # Ayin ilk gunu
        transaction_date = date(sale.year, sale.month, 1)

        record: dict[str, Any] = {
            "area_type": area_type,
            "area_name": area_name,
            "city": city,
            "district": district if district else None,
            "date": transaction_date,
            "transaction_count": sale.total_sales,
            "source": "TUIK",
            "provenance_version": f"TUIK-{sale.year}-{sale.month:02d}",
        }

        # -- HPI'dan tahmini m2 fiyati --
        hpi_key = f"{sale.year}-{sale.month:02d}"
        if hpi_key in hpi_lookup:
            record["avg_price_sqm"] = _estimate_price_per_sqm(
                hpi_index=hpi_lookup[hpi_key],
                base_price=Decimal("30000"),  # Turkiye geneli baz fiyat (TL/m2)
            )

        records.append(record)

    logger.debug(
        "price_history_normalized",
        city=city,
        district=district,
        record_count=len(records),
    )

    return records


def _estimate_price_per_sqm(
    hpi_index: float,
    base_price: Decimal,
    base_index: float = 100.0,
) -> Decimal:
    """
    HPI endeksinden tahmini m2 fiyati hesapla.

    Formul: base_price * (hpi_index / base_index)

    Args:
        hpi_index: Guncel HPI endeks degeri
        base_price: Baz donem m2 fiyati (TL)
        base_index: Baz donem endeks degeri (varsayilan 100.0)

    Returns:
        Tahmini m2 fiyati (Decimal)
    """
    if base_index == 0:
        return base_price

    ratio = _safe_decimal(hpi_index) / _safe_decimal(base_index)
    estimated = base_price * ratio
    return estimated.quantize(Decimal("0.01"))
