"""
Emlak Teknoloji Platformu - Valuations Schemas

Emsal bulma (comparable) ve ML degerleme istek/yanit Pydantic modelleri.
"""

from __future__ import annotations

from datetime import datetime  # noqa: TC003 — Pydantic resolves datetime at runtime

from pydantic import BaseModel, Field

# =====================================================================
# ML Degerleme (Valuation) Schemas
# =====================================================================


class ValuationRequest(BaseModel):
    """ML model ile fiyat tahmini istegi."""

    district: str = Field(
        ..., min_length=1, max_length=100, description="Ilce adi"
    )
    neighborhood: str = Field(
        ..., min_length=1, max_length=100, description="Mahalle adi"
    )
    property_type: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description="Mulk tipi: Daire, Villa, Mustakil, IsYeri",
    )
    net_sqm: float = Field(gt=0, le=1000, description="Net metrekare")
    gross_sqm: float = Field(gt=0, le=2000, description="Brut metrekare")
    room_count: int = Field(ge=1, le=10, description="Oda sayisi")
    living_room_count: int = Field(ge=0, le=5, description="Salon sayisi")
    floor: int = Field(ge=-2, le=50, description="Bulundugu kat")
    total_floors: int = Field(ge=1, le=60, description="Toplam kat sayisi")
    building_age: int = Field(ge=0, le=100, description="Bina yasi")
    heating_type: str = Field(
        ..., min_length=1, max_length=50, description="Isitma tipi"
    )

    def to_model_input(self) -> dict:
        """Pydantic modelini ML model input dict'ine donustur."""
        return self.model_dump()


class ValuationResponse(BaseModel):
    """ML model fiyat tahmini yaniti — emsal karsilastirma ve kota bilgisi icerir."""

    estimated_price: int = Field(description="Tahmini fiyat (TL)")
    min_price: int = Field(description="Alt sinir fiyat (TL)")
    max_price: int = Field(description="Ust sinir fiyat (TL)")
    confidence: float = Field(
        ge=0, le=1, description="Guven skoru (0-1)"
    )
    price_per_sqm: int = Field(description="m2 birim fiyat (TL)")
    latency_ms: int = Field(description="Tahmin suresi (ms)")
    model_version: str = Field(description="Kullanilan model versiyonu")
    prediction_id: str = Field(description="PredictionLog kayit ID")

    # Emsal karsilastirma sonuclari
    comparables: list[ComparableResult] = Field(
        default_factory=list,
        description="Otomatik bulunan emsal mulkler",
    )

    # Kota bilgisi
    quota_remaining: int = Field(
        default=-1,
        description="Kalan degerleme hakki (-1 = sinirsiz)",
    )
    quota_limit: int = Field(
        default=-1,
        description="Aylik toplam kota (-1 = sinirsiz)",
    )

    # Anomali uyarisi
    anomaly_warning: str | None = Field(
        default=None,
        description="Fiyat anomali uyarisi (z-score > 2.0 ise dolar, yoksa None)",
    )


# =====================================================================
# Emsal (Comparable) Schemas
# =====================================================================


class ComparableRequest(BaseModel):
    """Emsal arama istegi."""

    district: str = Field(..., min_length=1, max_length=100, description="Ilce adi")
    property_type: str = Field(
        ...,
        min_length=1,
        max_length=30,
        description="Mulk tipi: Daire, Villa, Mustakil, IsYeri",
    )
    net_sqm: float = Field(gt=0, le=1000, description="Net metrekare")
    room_count: int = Field(ge=1, le=10, description="Oda sayisi")
    building_age: int = Field(ge=0, le=100, description="Bina yasi")
    lat: float | None = Field(default=None, ge=-90, le=90, description="Enlem")
    lon: float | None = Field(default=None, ge=-180, le=180, description="Boylam")


class ComparableItem(BaseModel):
    """Tek bir emsal mulk bilgisi (comparables endpoint)."""

    property_id: str | None = None
    district: str
    net_sqm: float
    price: int
    building_age: int
    room_count: int
    distance_km: float | None = None
    similarity_score: float = Field(ge=0, le=100, description="Benzerlik skoru 0-100")


class ComparableResult(BaseModel):
    """
    Zenginlestirilmis emsal bilgisi (valuation endpoint).

    ComparableItem'dan farki: price_diff_percent ve address alanlari icerir.
    Degerleme raporu icinde emsal karsilastirma verisi olarak kullanilir.
    """

    property_id: str = Field(description="Emsal mulk ID")
    distance_km: float | None = Field(
        default=None, description="Hedef mulke mesafe (km)"
    )
    price_diff_percent: float = Field(
        description="Tahminden fiyat farki yuzde: ((emsal-tahmin)/tahmin*100)"
    )
    similarity_score: float = Field(
        ge=0, le=100, description="Benzerlik skoru 0-100"
    )
    address: str | None = Field(default=None, description="Emsal mulk adresi")
    price: int = Field(description="Emsal mulk fiyati (TL)")
    sqm: float = Field(description="Emsal mulk net m2")
    rooms: str | None = Field(default=None, description="Oda sayisi (orn: 3+1)")


class ComparableResponse(BaseModel):
    """Emsal arama yaniti."""

    comparables: list[ComparableItem]
    area_stats: dict | None = None
    total_found: int


# =====================================================================
# GET Endpoint Response Schemas
# =====================================================================


class ValuationListItem(BaseModel):
    """Degerleme gecmisi listesi icin ozet bilgi."""

    id: str = Field(description="PredictionLog kayit ID")
    predicted_price: int = Field(description="Tahmini fiyat (TL)")
    confidence_low: int = Field(description="Alt sinir fiyat (TL)")
    confidence_high: int = Field(description="Ust sinir fiyat (TL)")
    created_at: datetime = Field(description="Degerleme tarihi")
    model_version: str = Field(description="Kullanilan model versiyonu")


class ValuationListResponse(BaseModel):
    """Sayfali degerleme gecmisi yaniti."""

    items: list[ValuationListItem]
    total: int = Field(description="Toplam kayit sayisi")
    limit: int = Field(description="Sayfa basina kayit")
    offset: int = Field(description="Baslangic indeksi")


class ValuationDetailResponse(BaseModel):
    """Tek bir degerlemenin tam detayi."""

    id: str = Field(description="PredictionLog kayit ID")
    predicted_price: int = Field(description="Tahmini fiyat (TL)")
    confidence_low: int = Field(description="Alt sinir fiyat (TL)")
    confidence_high: int = Field(description="Ust sinir fiyat (TL)")
    confidence: float | None = Field(default=None, description="Guven skoru (0-1)")
    model_version: str = Field(description="Kullanilan model versiyonu")
    latency_ms: int | None = Field(default=None, description="Tahmin suresi (ms)")
    input_features: dict = Field(description="Model girdi ozellikleri")
    output_data: dict = Field(description="Model cikti verisi")
    created_at: datetime = Field(description="Degerleme tarihi")


class AreaPriceComparisonResponse(BaseModel):
    """Bolge m2 fiyat karsilastirma yaniti."""

    district: str = Field(description="Ilce adi")
    avg_price_per_sqm: float | None = Field(
        default=None, description="Ortalama m2 satis fiyati (TL)"
    )
    avg_rent_per_sqm: float | None = Field(
        default=None, description="Ortalama m2 kira fiyati (TL)"
    )
    trend: float | None = Field(
        default=None, description="Son 6 aylik fiyat trendi (%)"
    )
    listing_count: int | None = Field(
        default=None, description="Aktif ilan sayisi"
    )
    investment_score: float | None = Field(
        default=None, description="Yatirim potansiyeli skoru (0-100)"
    )
