"""
Emlak Teknoloji Platformu - Areas Schemas

Bolge analiz endpoint'leri icin Pydantic modelleri.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TrendItem(BaseModel):
    """Tek bir ayin fiyat trendi verisi."""

    month: str = Field(description="Ay (YYYY-MM formati)")
    avg_price_sqm: float | None = Field(
        default=None, description="Ortalama m2 fiyat (TL)"
    )
    min_price_sqm: float | None = Field(
        default=None, description="Minimum m2 fiyat (TL)"
    )
    max_price_sqm: float | None = Field(
        default=None, description="Maksimum m2 fiyat (TL)"
    )
    sample_count: int | None = Field(
        default=None, description="Orneklem sayisi (ilan/islem)"
    )


class PriceTrendResponse(BaseModel):
    """Ilce bazli fiyat trendi yaniti."""

    district: str = Field(description="Ilce adi")
    type: str = Field(description="Islem tipi: sale veya rent")
    months: int = Field(description="Istenen ay sayisi")
    trends: list[TrendItem] = Field(
        default_factory=list, description="Aylik trend verileri"
    )
    change_pct: float | None = Field(
        default=None,
        description="Ilk ve son ay arasindaki degisim yuzdesi",
    )


class InvestmentMetrics(BaseModel):
    """Yatirim metrikleri."""

    kira_verimi: float | None = Field(
        default=None,
        description="Yillik kira verimi yuzdesi: (aylik_kira * 12 / satis_fiyati) * 100",
    )
    amortisman_yil: float | None = Field(
        default=None,
        description="Amortisman suresi (yil): satis_fiyati / (aylik_kira * 12)",
    )


class CompareAreaItem(BaseModel):
    """Karsilastirma icindeki tek bir ilce verisi."""

    district: str = Field(description="Ilce adi")
    avg_price_sqm_sale: float | None = Field(
        default=None, description="Ortalama m2 satis fiyati (TL)"
    )
    avg_price_sqm_rent: float | None = Field(
        default=None, description="Ortalama m2 kira fiyati (TL)"
    )
    population: int | None = Field(default=None, description="Ilce nufusu")
    investment_score: float | None = Field(
        default=None, description="Yatirim potansiyeli skoru (0-100)"
    )
    transport_score: float | None = Field(
        default=None, description="Ulasim skoru (0-100)"
    )
    amenity_score: float | None = Field(
        default=None, description="Yasam kolayligi skoru (0-100)"
    )
    investment_metrics: InvestmentMetrics = Field(
        description="Hesaplanan yatirim metrikleri (kira_verimi, amortisman_yil)"
    )


class CompareResponse(BaseModel):
    """Birden fazla ilceyi yan yana karsilastirma yaniti."""

    areas: list[CompareAreaItem] = Field(description="Karsilastirilan ilce verileri")
    count: int = Field(description="Karsilastirilan ilce sayisi")


class AreaDetailResponse(BaseModel):
    """Ilce detay bilgisi yaniti."""

    city: str = Field(description="Sehir adi")
    district: str = Field(description="Ilce adi")
    avg_price_sqm_sale: float | None = Field(
        default=None, description="Ortalama m2 satis fiyati (TL)"
    )
    avg_price_sqm_rent: float | None = Field(
        default=None, description="Ortalama m2 kira fiyati (TL)"
    )
    price_trend_6m: float | None = Field(
        default=None, description="Son 6 aylik fiyat degisim yuzdesi"
    )
    population: int | None = Field(default=None, description="Ilce nufusu")
    listing_count: int | None = Field(default=None, description="Aktif ilan sayisi")
    transport_score: float | None = Field(
        default=None, description="Ulasim skoru (0-100)"
    )
    amenity_score: float | None = Field(
        default=None, description="Yasam kolayligi skoru (0-100)"
    )
    investment_score: float | None = Field(
        default=None, description="Yatirim potansiyeli skoru (0-100)"
    )
    investment_metrics: InvestmentMetrics = Field(
        description="Hesaplanan yatirim metrikleri"
    )
    # ─── Demografik Veriler ─────────────────────────────────────────
    median_age: float | None = Field(
        default=None, description="Medyan yas"
    )
    population_density: int | None = Field(
        default=None, description="Nufus yogunlugu (kisi/km2)"
    )
    age_distribution: dict[str, float] | None = Field(
        default=None,
        description="Yas dagilimi: {'0-14': 14.2, '15-24': 12.8, '25-44': 35.1, '45-64': 25.3, '65+': 12.6}",
    )


class DemographicsResponse(BaseModel):
    """Ilce demografik verileri yaniti."""

    district: str = Field(description="Ilce adi")
    population: int | None = Field(default=None, description="Ilce nufusu")
    median_age: float | None = Field(default=None, description="Medyan yas")
    population_density: int | None = Field(
        default=None, description="Nufus yogunlugu (kisi/km2)"
    )
    household_count: int | None = Field(default=None, description="Hane sayisi")
    avg_household_size: float | None = Field(
        default=None, description="Ortalama hane buyuklugu"
    )
    age_distribution: dict[str, float] | None = Field(
        default=None,
        description="Yas dagilimi: {'0-14': 14.2, '15-24': 12.8, '25-44': 35.1, '45-64': 25.3, '65+': 12.6}",
    )
