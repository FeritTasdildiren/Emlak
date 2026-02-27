"""
Emlak Teknoloji Platformu - Showcase Schemas

Vitrin (Showcase) modulu icin Pydantic veri modelleri.
API request/response serialization.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ================================================================
# Request Modelleri
# ================================================================


class ShowcaseCreate(BaseModel):
    """Yeni vitrin olusturma istegi."""

    title: str = Field(
        min_length=2,
        max_length=200,
        description="Vitrin basligi",
    )
    description: str | None = Field(
        default=None,
        description="Vitrin aciklamasi",
    )
    selected_properties: list[str] = Field(
        description="Secili ilan UUID listesi",
    )
    agent_phone: str | None = Field(
        default=None,
        max_length=20,
        description="Danisman telefon numarasi",
    )
    agent_email: str | None = Field(
        default=None,
        max_length=200,
        description="Danisman e-posta adresi",
    )
    agent_whatsapp: str | None = Field(
        default=None,
        max_length=20,
        description="Danisman WhatsApp numarasi",
    )
    theme: str = Field(
        default="default",
        max_length=20,
        description="Vitrin temasi: default, modern, classic vb.",
    )


class ShowcaseUpdate(BaseModel):
    """Vitrin guncelleme istegi. Sadece gonderilen alanlar guncellenir."""

    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
        description="Vitrin basligi",
    )
    description: str | None = Field(
        default=None,
        description="Vitrin aciklamasi",
    )
    selected_properties: list[str] | None = Field(
        default=None,
        description="Secili ilan UUID listesi",
    )
    agent_phone: str | None = Field(
        default=None,
        max_length=20,
        description="Danisman telefon numarasi",
    )
    agent_email: str | None = Field(
        default=None,
        max_length=200,
        description="Danisman e-posta adresi",
    )
    agent_whatsapp: str | None = Field(
        default=None,
        max_length=20,
        description="Danisman WhatsApp numarasi",
    )
    theme: str | None = Field(
        default=None,
        max_length=20,
        description="Vitrin temasi",
    )
    is_active: bool | None = Field(
        default=None,
        description="Vitrin aktif mi",
    )


# ================================================================
# Response Modelleri
# ================================================================


class ShowcaseResponse(BaseModel):
    """Tek vitrin yaniti (detay)."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Vitrin UUID")
    title: str = Field(description="Vitrin basligi")
    slug: str = Field(description="Public URL slug")
    description: str | None = Field(default=None, description="Vitrin aciklamasi")
    selected_properties: list = Field(default_factory=list, description="Secili ilan UUID listesi")
    agent_phone: str | None = Field(default=None, description="Danisman telefon")
    agent_email: str | None = Field(default=None, description="Danisman e-posta")
    agent_whatsapp: str | None = Field(default=None, description="Danisman WhatsApp")
    theme: str = Field(description="Vitrin temasi")
    is_active: bool = Field(description="Vitrin aktif mi")
    views_count: int = Field(description="Goruntulenme sayisi")
    created_at: datetime = Field(description="Olusturulma zamani")
    updated_at: datetime = Field(description="Son guncelleme zamani")


class ShowcaseListItem(BaseModel):
    """Vitrin listesi ogesi (ozet)."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Vitrin UUID")
    title: str = Field(description="Vitrin basligi")
    slug: str = Field(description="Public URL slug")
    is_active: bool = Field(description="Vitrin aktif mi")
    views_count: int = Field(description="Goruntulenme sayisi")
    created_at: datetime = Field(description="Olusturulma zamani")


class ShowcaseListResponse(BaseModel):
    """Vitrin listesi yaniti."""

    items: list[ShowcaseListItem] = Field(description="Vitrin listesi")
    total: int = Field(description="Toplam vitrin sayisi")


class PropertySummary(BaseModel):
    """Vitrin icindeki ilan ozeti (public gorunum)."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Ilan UUID")
    title: str | None = Field(default=None, description="Ilan basligi")
    listing_type: str | None = Field(default=None, description="Ilan tipi: sale, rent")
    property_type: str | None = Field(default=None, description="Gayrimenkul tipi")
    price: float | None = Field(default=None, description="Fiyat (TRY)")
    currency: str | None = Field(default=None, description="Para birimi")
    city: str | None = Field(default=None, description="Sehir")
    district: str | None = Field(default=None, description="Ilce")
    neighborhood: str | None = Field(default=None, description="Mahalle")
    net_sqm: float | None = Field(default=None, description="Net m2")
    gross_sqm: float | None = Field(default=None, description="Brut m2")
    room_count: str | None = Field(default=None, description="Oda sayisi (orn: 3+1)")
    building_age: int | None = Field(default=None, description="Bina yasi")
    floor_number: int | None = Field(default=None, description="Kat numarasi")
    total_floors: int | None = Field(default=None, description="Toplam kat")
    photo_urls: list[str] = Field(default_factory=list, description="Fotograf URL'leri")


class ShowcasePublicResponse(BaseModel):
    """Vitrin public gorunumu (slug ile erisim)."""

    model_config = ConfigDict(from_attributes=True)

    slug: str = Field(description="Public URL slug")
    title: str = Field(description="Vitrin basligi")
    description: str | None = Field(default=None, description="Vitrin aciklamasi")
    agent_phone: str | None = Field(default=None, description="Danisman telefon")
    agent_email: str | None = Field(default=None, description="Danisman e-posta")
    agent_whatsapp: str | None = Field(default=None, description="Danisman WhatsApp")
    agent_photo_url: str | None = Field(default=None, description="Danisman profil foto URL")
    theme: str = Field(description="Vitrin temasi")
    properties: list[PropertySummary] = Field(
        default_factory=list,
        description="Vitrin icindeki ilanlar (detayli)",
    )
    views_count: int = Field(description="Goruntulenme sayisi")


# ================================================================
# Paylasim Agi (Shared Showcases)
# ================================================================


class SharedShowcaseItem(BaseModel):
    """Paylasim agindaki vitrin ozeti (diger ofislerden)."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Vitrin UUID")
    title: str = Field(description="Vitrin basligi")
    slug: str = Field(description="Public URL slug")
    description: str | None = Field(default=None, description="Vitrin aciklamasi")
    agent_name: str = Field(description="Danisman adi")
    agent_phone: str | None = Field(default=None, description="Danisman telefon")
    property_count: int = Field(description="Secili ilan sayisi")
    views_count: int = Field(description="Goruntulenme sayisi")
    office_name: str | None = Field(default=None, description="Ofis adi")
    created_at: datetime = Field(description="Olusturulma zamani")


class SharedShowcaseListResponse(BaseModel):
    """Paylasim agi vitrin listesi yaniti."""

    items: list[SharedShowcaseItem] = Field(description="Paylasilan vitrinler")
    total: int = Field(description="Toplam paylasilan vitrin sayisi")


# ================================================================
# WhatsApp Click-to-Chat
# ================================================================


class WhatsAppLinkResponse(BaseModel):
    """WhatsApp click-to-chat link yaniti."""

    whatsapp_url: str = Field(description="WhatsApp click-to-chat URL")


# ================================================================
# Paylasim Toggle (Property sharing)
# ================================================================


class PropertySharingUpdate(BaseModel):
    """Ilan paylasim ayarlari guncelleme istegi."""

    is_shared: bool = Field(
        description="Ofisler arasi paylasima acik mi",
    )
    share_visibility: str = Field(
        default="private",
        description="Paylasim gorunurlugu: private, shared, public",
        pattern="^(private|shared|public)$",
    )


class PropertySharingResponse(BaseModel):
    """Ilan paylasim ayarlari yaniti."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Ilan UUID")
    is_shared: bool = Field(description="Paylasima acik mi")
    share_visibility: str = Field(description="Paylasim gorunurlugu")
