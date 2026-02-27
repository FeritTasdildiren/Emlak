"""
Emlak Teknoloji Platformu - Earthquake Schemas

Deprem risk ve bina guvenlik skoru istek/yanit Pydantic modelleri.
TBDY 2018 referansli zemin siniflandirmasi ve risk degerlendirmesi.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

# =====================================================================
# Ilce Deprem Risk Schemas (TASK-093)
# =====================================================================


class EarthquakeRiskResponse(BaseModel):
    """Ilce deprem risk bilgisi yaniti."""

    city: str = Field(description="Sehir adi")
    district: str = Field(description="Ilce adi")
    risk_score: float = Field(description="Genel deprem risk skoru (0-100)")
    risk_level: str = Field(
        description="Risk seviyesi: Dusuk, Orta, Yuksek, Cok Yuksek"
    )
    pga_value: float | None = Field(
        default=None, description="Peak Ground Acceleration (g cinsinden)"
    )
    soil_class: str | None = Field(
        default=None, description="TBDY zemin sinifi: ZA, ZB, ZC, ZD, ZE"
    )
    fault_distance_km: float | None = Field(
        default=None, description="En yakin fay hattina mesafe (km)"
    )
    building_code_era: str | None = Field(
        default=None,
        description="Yapi yonetmeligi donemi: pre_1999, 1999_2018, post_2018",
    )


# =====================================================================
# Enum Tanimlari — Bina Guvenlik Skoru
# =====================================================================


class SoilClass(StrEnum):
    """TBDY 2018 zemin siniflandirmasi."""

    ZA = "ZA"  # Saglam kaya
    ZB = "ZB"  # Kaya
    ZC = "ZC"  # Cok siki kum, cakil ve sert kil
    ZD = "ZD"  # Siki kum, cakil ve kati kil
    ZE = "ZE"  # Yumusak kil ve silt


class ConstructionType(StrEnum):
    """Yapi tipi."""

    BETONARME = "betonarme"
    CELIK = "celik"
    YIGMA = "yigma"
    AHSAP = "ahsap"


class RiskLevel(StrEnum):
    """Risk seviyesi."""

    LOW = "Dusuk"
    MEDIUM = "Orta"
    HIGH = "Yuksek"
    VERY_HIGH = "Cok Yuksek"


# =====================================================================
# Bina Guvenlik Skoru Schemas (TASK-094)
# =====================================================================


class BuildingScoreRequest(BaseModel):
    """Deprem bina guvenlik skoru istegi."""

    building_age: int = Field(
        ..., ge=0, le=200, description="Bina yasi (yil)"
    )
    floors: int = Field(
        ..., ge=1, le=100, description="Toplam kat sayisi"
    )
    soil_class: SoilClass = Field(
        ..., description="TBDY 2018 zemin sinifi (ZA-ZE)"
    )
    construction_type: ConstructionType | None = Field(
        default=None, description="Yapi tipi: betonarme, celik, yigma, ahsap"
    )
    has_retrofit: bool | None = Field(
        default=None, description="Guclendirme yapilmis mi"
    )


class BuildingScoreResult(BaseModel):
    """Deprem bina guvenlik skoru yaniti."""

    safety_score: float = Field(
        ge=0, le=100, description="Guvenlik skoru (0-100, yuksek = guvenli)"
    )
    risk_level: RiskLevel = Field(description="Risk seviyesi")
    color_code: str = Field(description="Renk kodu: green, yellow, orange, red")
    risk_factors: list[str] = Field(description="Tespit edilen risk faktorleri")
    recommendations: list[str] = Field(description="Oneriler listesi")
    disclaimer: str = Field(
        description="Yasal uyari metni",
    )
