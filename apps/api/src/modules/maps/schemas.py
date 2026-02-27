"""
Emlak Teknoloji Platformu - Maps Schemas

Harita endpoint'leri icin Pydantic v2 modelleri (GeoJSON).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

# ---------- GeoJSON Schemas ----------


class GeoJSONPoint(BaseModel):
    """GeoJSON Point geometrisi."""

    type: str = Field(default="Point")
    coordinates: list[float] = Field(
        description="[longitude, latitude]", min_length=2, max_length=2
    )


class GeoJSONFeatureProperties(BaseModel):
    """Harita property feature ozellikleri."""

    id: str = Field(description="Property UUID")
    title: str = Field(description="Ilan basligi")
    price: float = Field(description="Fiyat (TL)")
    listing_type: str = Field(description="Ilan tipi: sale veya rent")
    property_type: str = Field(description="Emlak tipi")
    rooms: str | None = Field(default=None, description="Oda sayisi (ör: 3+1)")
    net_area: float | None = Field(default=None, description="Net alan (m2)")
    district: str = Field(description="Ilce")


class GeoJSONFeature(BaseModel):
    """GeoJSON Feature."""

    type: str = Field(default="Feature")
    geometry: GeoJSONPoint
    properties: GeoJSONFeatureProperties


class GeoJSONFeatureCollection(BaseModel):
    """GeoJSON FeatureCollection yaniti."""

    type: str = Field(default="FeatureCollection")
    features: list[GeoJSONFeature] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Ek bilgiler: toplam sayi, bbox, vb.",
    )


# ---------- Heatmap Schemas ----------


class HeatmapPoint(BaseModel):
    """Heatmap tekil veri noktasi."""

    lat: float = Field(description="Enlem")
    lon: float = Field(description="Boylam")
    intensity: float = Field(description="Yogunluk degeri (normalize edilmis)")


class HeatmapResponse(BaseModel):
    """Ilce bazli heatmap yaniti."""

    points: list[HeatmapPoint] = Field(
        default_factory=list, description="Heatmap veri noktalari"
    )
    min_value: float | None = Field(
        default=None, description="Minimum m2 fiyat (TL)"
    )
    max_value: float | None = Field(
        default=None, description="Maksimum m2 fiyat (TL)"
    )
