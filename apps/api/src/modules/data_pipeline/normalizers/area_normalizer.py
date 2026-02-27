"""
Emlak Teknoloji Platformu - Area Analysis Normalizer

TUIK ve TCMB API response'larini AreaAnalysis entity alanlarina normalize eder.
Birden fazla API kaynagini tek bir dict'e birlestirerek UPSERT'e hazirlar.

Kullanim:
    from src.modules.data_pipeline.normalizers import normalize_area_analysis, safe_decimal

    data = normalize_area_analysis(
        city="Istanbul",
        district="Kadikoy",
        population_data=pop_data,
        demographics_data=demo_data,
        housing_sales=sales,
        hpi_data=hpi,
    )
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

import structlog

from src.modules.data_pipeline.schemas.api_responses import (
    DemographicsData,
    HousingPriceIndexData,
    HousingSaleData,
    PopulationData,
)

logger = structlog.get_logger("data_pipeline.normalizers.area")


def safe_decimal(value: Any, default: str = "0.00") -> Decimal:
    """
    float/int/str degerini guvenli Decimal'e donustur.

    IEEE-754 precision kaybi onlemek icin float ONCE str'ye cevirilir.
    Ornek: float(0.1) = 0.1000000000000000055511151231257827021181583404541015625
           Decimal(str(0.1)) = Decimal('0.1')

    Args:
        value: Donusturulecek deger
        default: Parse edilemezse kullanilacak varsayilan

    Returns:
        Decimal
    """
    if value is None:
        return Decimal(default)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def normalize_area_analysis(
    city: str,
    district: str,
    population_data: PopulationData | None,
    demographics_data: DemographicsData | None,
    housing_sales: list[HousingSaleData] | None,
    hpi_data: HousingPriceIndexData | None,
    neighborhood: str | None = None,
) -> dict[str, Any]:
    """
    Birden fazla API response'u AreaAnalysis INSERT/UPDATE dict'ine donustur.

    Args:
        city: Il adi
        district: Ilce adi
        population_data: TUIK nufus verisi (opsiyonel)
        demographics_data: TUIK demografik verisi (opsiyonel)
        housing_sales: TUIK konut satis verileri (opsiyonel)
        hpi_data: TCMB konut fiyat endeksi (opsiyonel)
        neighborhood: Mahalle adi (opsiyonel)

    Returns:
        Dict -- SQLAlchemy UPSERT icin hazir alan:deger ciftleri.
        Ornek: {
            "city": "Istanbul",
            "district": "Kadikoy",
            "population": 484957,
            "demographics": {"age_0_14_pct": 14.2, ...},
            "avg_price_sqm_sale": Decimal("52300.00"),
            ...
        }
    """
    result: dict[str, Any] = {
        "city": city,
        "district": district,
        "neighborhood": neighborhood,
    }

    # -- Nufus --
    if population_data is not None:
        result["population"] = population_data.total_population
    else:
        result["population"] = 0

    # -- Demografik veriler --
    if demographics_data is not None:
        result["demographics"] = _build_demographics_jsonb(demographics_data)
    else:
        result["demographics"] = {}

    # -- Fiyat verisi (HPI proxy) --
    if hpi_data is not None:
        result["avg_price_sqm_sale"] = safe_decimal(hpi_data.index_value)
    else:
        result["avg_price_sqm_sale"] = safe_decimal(None, "0.00")

    # -- Fiyat trendi (son 6 ay satis verilerinden) --
    if housing_sales:
        trend = _calculate_price_trend(housing_sales)
        if trend is not None:
            result["price_trend_6m"] = trend

    logger.debug(
        "area_analysis_normalized",
        city=city,
        district=district,
        population=result.get("population"),
        has_demographics=demographics_data is not None,
        has_hpi=hpi_data is not None,
        has_sales=bool(housing_sales),
    )

    return result


def _build_demographics_jsonb(demo: DemographicsData) -> dict[str, Any]:
    """
    DemographicsData Pydantic modeli -> demographics JSONB alani.

    Yuzdelik degerler float olarak saklanir (JSONB'de Decimal yok).
    None degerler atlanir.
    """
    data: dict[str, Any] = {
        "year": demo.year,
        "age_0_14_pct": demo.age_0_14_pct,
        "age_15_24_pct": demo.age_15_24_pct,
        "age_25_44_pct": demo.age_25_44_pct,
        "age_45_64_pct": demo.age_45_64_pct,
        "age_65_plus_pct": demo.age_65_plus_pct,
        "university_graduate_pct": demo.university_graduate_pct,
        "high_school_graduate_pct": demo.high_school_graduate_pct,
    }

    if demo.median_income is not None:
        data["median_income"] = demo.median_income

    return data


def _calculate_price_trend(sales_data: list[HousingSaleData]) -> Decimal | None:
    """
    Son 6 aylik satis verilerinden fiyat trendi hesapla.

    Basit yaklasim: Son 3 ay toplam satisi / onceki 3 ay toplam satisi - 1
    Bu oran satis hacmindeki degisimi gosterir (fiyat proxy'si).

    Args:
        sales_data: Kronolojik siralanmis HousingSaleData listesi

    Returns:
        Decimal yuzde degisim veya None (yetersiz veri)
    """
    if len(sales_data) < 6:
        return None

    # Son 6 kaydi al (kronolojik sira varsayimi)
    recent = sales_data[-6:]

    older_total = sum(s.total_sales for s in recent[:3])
    newer_total = sum(s.total_sales for s in recent[3:])

    if older_total == 0:
        return None

    change_pct = ((newer_total - older_total) / older_total) * 100
    return safe_decimal(change_pct).quantize(Decimal("0.01"))
