"""
Emlak Teknoloji Platformu - Listing Assistant Schemas

Pydantic v2 modeller: ilan metni uretim istegi/yaniti, ton bilgisi, yeniden uretim.

Referans: TASK-118 (S8.2 + S8.3)
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ================================================================
# Tone Info
# ================================================================


class ToneInfo(BaseModel):
    """Tek bir ilan tonu bilgisi."""

    id: str = Field(
        ...,
        description="Ton ID: kurumsal, samimi, acil",
        examples=["kurumsal"],
    )
    name_tr: str = Field(..., description="Turkce ton adi")
    description: str = Field(..., description="Ton aciklamasi")
    example_phrase: str = Field(
        ...,
        description="Ornek cumle — tonun nasil hissettirdigini gosterir",
    )


class ToneListResponse(BaseModel):
    """Tum tonlarin listesi."""

    tones: list[ToneInfo]
    count: int = Field(..., description="Toplam ton sayisi")


# ================================================================
# Listing Text Request
# ================================================================


class ListingTextRequest(BaseModel):
    """Ilan metni uretim istegi."""

    # Zorunlu alanlar
    property_type: str = Field(
        ...,
        description="Mulk tipi: daire, villa, rezidans, mustakil, arsa",
        examples=["daire"],
    )
    district: str = Field(
        ...,
        description="Ilce adi",
        examples=["Kadikoy"],
    )
    neighborhood: str = Field(
        ...,
        description="Mahalle adi",
        examples=["Caferaga"],
    )
    net_sqm: int = Field(
        ...,
        gt=0,
        description="Net metrekare",
        examples=[120],
    )
    room_count: str = Field(
        ...,
        description="Oda sayisi: 1+1, 2+1, 3+1, 4+1, 5+1, 6+ vb.",
        examples=["3+1"],
    )
    price: int = Field(
        ...,
        gt=0,
        description="Satis fiyati (TL)",
        examples=[4500000],
    )

    # Opsiyonel alanlar
    gross_sqm: int | None = Field(
        default=None,
        gt=0,
        description="Brut metrekare",
    )
    floor: int | None = Field(
        default=None,
        description="Bulundugu kat",
    )
    total_floors: int | None = Field(
        default=None,
        gt=0,
        description="Toplam kat sayisi",
    )
    building_age: int | None = Field(
        default=None,
        ge=0,
        description="Bina yasi",
    )
    heating_type: str | None = Field(
        default=None,
        description="Isitma tipi: dogalgaz, merkezi, kombi, soba, klima, yerden_isitma",
    )
    has_elevator: bool | None = Field(default=None, description="Asansor var mi?")
    has_parking: bool | None = Field(default=None, description="Otopark var mi?")
    has_balcony: bool | None = Field(default=None, description="Balkon var mi?")
    has_garden: bool | None = Field(default=None, description="Bahce var mi?")
    has_pool: bool | None = Field(default=None, description="Havuz var mi?")
    is_furnished: bool | None = Field(default=None, description="Esyali mi?")
    has_security: bool | None = Field(default=None, description="Guvenlik var mi?")
    view_type: str | None = Field(
        default=None,
        description="Manzara tipi: deniz, bogaz, orman, sehir, gol",
    )
    additional_notes: str | None = Field(
        default=None,
        max_length=500,
        description="Ek notlar (orn. 'yeni boyandi, sahibinden')",
    )

    # Ton secimi
    tone: Literal["kurumsal", "samimi", "acil"] = Field(
        default="kurumsal",
        description="Ilan metni tonu: kurumsal, samimi, acil",
    )


# ================================================================
# Listing Text Response
# ================================================================


class ListingTextResponse(BaseModel):
    """Ilan metni uretim yaniti."""

    title: str = Field(
        ...,
        description="SEO-optimize edilmis ilan basligi",
        examples=["3+1 Daire Caferaga Kadikoy - Deniz Manzarali"],
    )
    description: str = Field(
        ...,
        description="Detayli ilan aciklamasi (300-600 kelime)",
    )
    highlights: list[str] = Field(
        ...,
        description="One cikan ozellikler listesi (3-6 madde)",
        examples=[["Deniz manzarasi", "Metro yakininda", "Yeni bina"]],
    )
    seo_keywords: list[str] = Field(
        ...,
        description="SEO anahtar kelimeler (5-10 adet)",
        examples=[["kadikoy daire", "satilik 3+1", "deniz manzarali"]],
    )
    tone_used: str = Field(
        ...,
        description="Kullanilan ton",
        examples=["kurumsal"],
    )
    token_usage: int = Field(
        ...,
        ge=0,
        description="Harcanan tahmini token sayisi",
    )


# ================================================================
# Regenerate Request
# ================================================================


class RegenerateRequest(BaseModel):
    """Farkli tonla yeniden uretim istegi — kota tuketmez."""

    # Orijinal ilan bilgileri (ayni body)
    property_type: str = Field(...)
    district: str = Field(...)
    neighborhood: str = Field(...)
    net_sqm: int = Field(..., gt=0)
    room_count: str = Field(...)
    price: int = Field(..., gt=0)

    gross_sqm: int | None = Field(default=None, gt=0)
    floor: int | None = Field(default=None)
    total_floors: int | None = Field(default=None, gt=0)
    building_age: int | None = Field(default=None, ge=0)
    heating_type: str | None = Field(default=None)
    has_elevator: bool | None = Field(default=None)
    has_parking: bool | None = Field(default=None)
    has_balcony: bool | None = Field(default=None)
    has_garden: bool | None = Field(default=None)
    has_pool: bool | None = Field(default=None)
    is_furnished: bool | None = Field(default=None)
    has_security: bool | None = Field(default=None)
    view_type: str | None = Field(default=None)
    additional_notes: str | None = Field(default=None, max_length=500)

    # Yeni ton
    tone: Literal["kurumsal", "samimi", "acil"] = Field(
        ...,
        description="Yeniden uretim icin secilen ton",
    )
