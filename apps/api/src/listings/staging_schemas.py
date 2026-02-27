"""
Emlak Teknoloji Platformu - Virtual Staging Schemas

Pydantic v2 modeller: oda analizi, sahneleme istegi/yaniti, tarz bilgisi.

Referans: TASK-115 (S8.5 + S8.6)
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# ================================================================
# Room Analysis
# ================================================================


class RoomAnalysisResponse(BaseModel):
    """Oda analiz sonucu — GPT-5-mini Vision ciktisi."""

    room_type: str = Field(
        ...,
        description=(
            "Oda tipi: salon, yatak_odasi, mutfak, banyo, "
            "cocuk_odasi, calisma_odasi, yemek_odasi, antre"
        ),
        examples=["salon"],
    )
    is_empty: bool = Field(
        ...,
        description="Oda bos mu? True ise sahneleme yapilabilir.",
    )
    floor_type: str = Field(
        default="bilinmiyor",
        description="Zemin tipi: parke, seramik, laminat, mermer, hali, beton, bilinmiyor",
        examples=["parke"],
    )
    estimated_size: str = Field(
        default="orta",
        description="Tahmini oda boyutu: kucuk, orta, buyuk",
        examples=["orta"],
    )
    wall_color: str = Field(
        default="beyaz",
        description="Duvar rengi tahmini",
        examples=["beyaz"],
    )
    natural_light: str = Field(
        default="orta",
        description="Dogal isik seviyesi: dusuk, orta, yuksek",
        examples=["orta"],
    )
    window_count: int = Field(
        default=0,
        ge=0,
        description="Tespit edilen pencere sayisi",
    )
    special_features: list[str] = Field(
        default_factory=list,
        description="Ozel ozellikler: somine, balkon, tavan kirisi vb.",
        examples=[["somine", "balkon"]],
    )


# ================================================================
# Style Info
# ================================================================


class StyleInfo(BaseModel):
    """Tek bir sahneleme tarzi bilgisi."""

    id: str = Field(..., description="Tarz ID: modern, klasik, minimalist vb.")
    name_tr: str = Field(..., description="Turkce tarz adi")
    description: str = Field(..., description="Tarz aciklamasi")


class StyleListResponse(BaseModel):
    """Tum tarzlarin listesi."""

    styles: list[StyleInfo]
    count: int = Field(..., description="Toplam tarz sayisi")


# ================================================================
# Staging Request / Response
# ================================================================


class StagingRequest(BaseModel):
    """Virtual staging istek modeli (form data ile de kullanilabilir)."""

    style: str = Field(
        ...,
        description="Sahneleme tarzi: modern, klasik, minimalist, skandinav, bohem, endustriyel",
        examples=["modern"],
    )


class StagedImageItem(BaseModel):
    """Tek bir sahnelenmiş görsel."""

    base64: str = Field(..., description="Base64 encode edilmis PNG gorsel")


class StagingResponse(BaseModel):
    """Virtual staging yanit modeli."""

    staged_images: list[StagedImageItem] = Field(
        ...,
        description="Sahnelenmiş gorsel(ler) — base64 PNG listesi",
    )
    room_analysis: RoomAnalysisResponse = Field(
        ...,
        description="Oda analiz sonucu",
    )
    style: str = Field(..., description="Uygulanan tarz")
    processing_time_ms: int = Field(
        ...,
        ge=0,
        description="Toplam islem suresi (milisaniye)",
    )
