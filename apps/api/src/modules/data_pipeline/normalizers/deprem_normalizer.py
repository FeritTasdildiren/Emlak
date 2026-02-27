"""
Emlak Teknoloji Platformu - Deprem Risk Normalizer

AFAD API response'larini DepremRisk entity alanlarina normalize eder.
PGA -> risk skoru donusumu, PostGIS WKT olusturma ve fay mesafesi hesaplama.

Kullanim:
    from src.modules.data_pipeline.normalizers import (
        normalize_deprem_risk, calculate_risk_score, build_point_wkt,
    )

    data = normalize_deprem_risk(
        city="Istanbul",
        district="Kadikoy",
        hazard_data=hazard,
        fault_data=faults,
        latitude=40.9927,
        longitude=29.0230,
    )
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any

import structlog

from src.modules.data_pipeline.schemas.api_responses import (
    EarthquakeHazardData,
    FaultData,
)

logger = structlog.get_logger("data_pipeline.normalizers.deprem")


def _safe_decimal(value: Any, default: str = "0.00") -> Decimal:
    """float/int/str -> guvenli Decimal. float -> str -> Decimal zinciri."""
    if value is None:
        return Decimal(default)
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return Decimal(default)


def normalize_deprem_risk(
    city: str,
    district: str,
    hazard_data: EarthquakeHazardData | None,
    fault_data: list[FaultData] | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
    neighborhood: str | None = None,
) -> dict[str, Any]:
    """
    AFAD response'u DepremRisk INSERT/UPDATE dict'ine donustur.

    Args:
        city: Il adi
        district: Ilce adi
        hazard_data: AFAD deprem tehlike parametreleri (opsiyonel)
        fault_data: Yakin fay hatlari (opsiyonel)
        latitude: Enlem (opsiyonel, hazard_data'dan da alinabilir)
        longitude: Boylam (opsiyonel, hazard_data'dan da alinabilir)
        neighborhood: Mahalle adi (opsiyonel)

    Returns:
        Dict -- PostGIS POINT WKT dahil.
        Ornek: {
            "city": "Istanbul",
            "district": "Kadikoy",
            "pga_value": Decimal("0.3214"),
            "risk_score": Decimal("60.54"),
            "soil_class": "ZC",
            "fault_distance_km": Decimal("12.30"),
            "location_wkt": "SRID=4326;POINT(29.0231 40.9927)",
            ...
        }
    """
    result: dict[str, Any] = {
        "city": city,
        "district": district,
        "neighborhood": neighborhood,
    }

    # -- Koordinatlar (hazard_data oncelikli, parametre fallback) --
    lat = latitude
    lon = longitude
    if hazard_data is not None:
        lat = lat or hazard_data.latitude
        lon = lon or hazard_data.longitude

    # -- PostGIS WKT --
    if lat is not None and lon is not None:
        result["location_wkt"] = build_point_wkt(lat, lon)
        result["latitude"] = lat
        result["longitude"] = lon

    # -- PGA ve Risk Skoru --
    if hazard_data is not None:
        pga_value = _safe_decimal(hazard_data.pga_475)
        result["pga_value"] = pga_value
        result["risk_score"] = calculate_risk_score(pga_value)
        result["soil_class"] = hazard_data.soil_class
    else:
        result["pga_value"] = _safe_decimal(None)
        result["risk_score"] = _safe_decimal(None)
        result["soil_class"] = None

    # -- Fay mesafesi --
    if fault_data:
        nearest = _nearest_fault_distance(fault_data)
        if nearest is not None:
            result["fault_distance_km"] = nearest

    logger.debug(
        "deprem_risk_normalized",
        city=city,
        district=district,
        pga=str(result.get("pga_value")),
        risk_score=str(result.get("risk_score")),
        soil_class=result.get("soil_class"),
    )

    return result


def calculate_risk_score(pga: Decimal) -> Decimal:
    """
    PGA degerini 0-100 risk skoruna donustur (lineer interpolasyon).

    PGA (g)     Risk Skoru
    0.0 - 0.1   0  - 20   (Cok dusuk)
    0.1 - 0.2   20 - 40   (Dusuk)
    0.2 - 0.3   40 - 60   (Orta)
    0.3 - 0.4   60 - 80   (Yuksek)
    0.4+        80 - 100  (Cok yuksek)

    Args:
        pga: Peak Ground Acceleration (g cinsinden), Decimal tipinde

    Returns:
        Decimal risk skoru (0.00 - 100.00)

    Examples:
        >>> calculate_risk_score(Decimal("0.05"))
        Decimal('10.00')
        >>> calculate_risk_score(Decimal("0.15"))
        Decimal('30.00')
        >>> calculate_risk_score(Decimal("0.4"))
        Decimal('80.00')
        >>> calculate_risk_score(Decimal("0.6"))
        Decimal('100.00')
    """
    if pga <= Decimal("0"):
        return Decimal("0.00")

    # PGA aralik tanimlari: (pga_min, pga_max, score_min, score_max)
    bands: list[tuple[Decimal, Decimal, Decimal, Decimal]] = [
        (Decimal("0.0"), Decimal("0.1"), Decimal("0"), Decimal("20")),
        (Decimal("0.1"), Decimal("0.2"), Decimal("20"), Decimal("40")),
        (Decimal("0.2"), Decimal("0.3"), Decimal("40"), Decimal("60")),
        (Decimal("0.3"), Decimal("0.4"), Decimal("60"), Decimal("80")),
    ]

    for pga_min, pga_max, score_min, score_max in bands:
        if pga_min <= pga < pga_max:
            ratio = (pga - pga_min) / (pga_max - pga_min)
            score = score_min + ratio * (score_max - score_min)
            return score.quantize(Decimal("0.01"))

    # PGA >= 0.4 -> 80-100 arasi (0.4-0.5 icin lineer, 0.5+ icin 100)
    if pga >= Decimal("0.5"):
        return Decimal("100.00")

    # 0.4 - 0.5 arasi lineer interpolasyon -> 80-100
    ratio = (pga - Decimal("0.4")) / Decimal("0.1")
    score = Decimal("80") + ratio * Decimal("20")
    return min(score.quantize(Decimal("0.01")), Decimal("100.00"))


def build_point_wkt(latitude: float, longitude: float) -> str:
    """
    PostGIS GEOGRAPHY POINT WKT olustur.

    Format: 'SRID=4326;POINT(lon lat)'
    DIKKAT: WKT POINT formatinda sira (longitude latitude) — (X Y) seklindedir.

    Args:
        latitude: Enlem (Y)
        longitude: Boylam (X)

    Returns:
        WKT string: "SRID=4326;POINT(lon lat)"
    """
    return f"SRID=4326;POINT({longitude} {latitude})"


def _nearest_fault_distance(faults: list[FaultData]) -> Decimal | None:
    """
    Fay listesinden en yakin fay mesafesini dondur.

    Args:
        faults: FaultData listesi (distance_km alani olan)

    Returns:
        En yakin fay mesafesi (km) veya None (bos liste)
    """
    if not faults:
        return None

    distances = [
        _safe_decimal(f.distance_km)
        for f in faults
        if f.distance_km is not None and f.distance_km >= 0
    ]

    if not distances:
        return None

    return min(distances)
