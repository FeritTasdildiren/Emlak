"""
Emlak Teknoloji Platformu - Customer Schemas

Müşteri modülü için Pydantic veri modelleri.
API request/response serialization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ================================================================
# Request Modelleri
# ================================================================


class CustomerCreate(BaseModel):
    """Yeni müşteri oluşturma isteği."""

    full_name: str = Field(
        min_length=2, max_length=200,
        description="Ad soyad",
    )
    phone: str | None = Field(
        default=None, max_length=20,
        description="Telefon numarası",
    )
    email: str | None = Field(
        default=None, max_length=255,
        description="E-posta adresi",
    )
    customer_type: Literal["buyer", "seller", "renter", "landlord"] = Field(
        default="buyer",
        description="Müşteri tipi",
    )
    budget_min: float | None = Field(
        default=None, ge=0,
        description="Minimum bütçe (TRY)",
    )
    budget_max: float | None = Field(
        default=None, ge=0,
        description="Maksimum bütçe (TRY)",
    )
    desired_rooms: str | None = Field(
        default=None, max_length=50,
        description="Tercih edilen oda sayısı (ör: 2+1, 3+1)",
    )
    desired_area_min: int | None = Field(
        default=None, ge=0,
        description="Minimum aranan alan (m²)",
    )
    desired_area_max: int | None = Field(
        default=None, ge=0,
        description="Maksimum aranan alan (m²)",
    )
    desired_districts: list[str] = Field(
        default_factory=list,
        description="Tercih edilen ilçeler",
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Müşteri etiketleri",
    )
    source: str | None = Field(
        default=None, max_length=50,
        description="Müşteri kaynağı (referans, ilan, vb.)",
    )
    notes: str | None = Field(
        default=None,
        description="Danışman notları",
    )


class CustomerUpdate(BaseModel):
    """Müşteri güncelleme isteği. Sadece gönderilen alanlar güncellenir."""

    full_name: str | None = Field(
        default=None, min_length=2, max_length=200,
        description="Ad soyad",
    )
    phone: str | None = Field(
        default=None, max_length=20,
        description="Telefon numarası",
    )
    email: str | None = Field(
        default=None, max_length=255,
        description="E-posta adresi",
    )
    budget_min: float | None = Field(
        default=None, ge=0,
        description="Minimum bütçe (TRY)",
    )
    budget_max: float | None = Field(
        default=None, ge=0,
        description="Maksimum bütçe (TRY)",
    )
    desired_rooms: str | None = Field(
        default=None, max_length=50,
        description="Tercih edilen oda sayısı",
    )
    desired_area_min: int | None = Field(
        default=None, ge=0,
        description="Minimum aranan alan (m²)",
    )
    desired_area_max: int | None = Field(
        default=None, ge=0,
        description="Maksimum aranan alan (m²)",
    )
    desired_districts: list[str] | None = Field(
        default=None,
        description="Tercih edilen ilçeler",
    )
    tags: list[str] | None = Field(
        default=None,
        description="Müşteri etiketleri",
    )
    notes: str | None = Field(
        default=None,
        description="Danışman notları",
    )


class LeadStatusUpdate(BaseModel):
    """Lead status güncelleme isteği."""

    status: Literal["cold", "warm", "hot", "converted", "lost"] = Field(
        description="Yeni lead durumu",
    )


# ================================================================
# Response Modelleri
# ================================================================


class CustomerResponse(BaseModel):
    """Tek müşteri yanıtı."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Müşteri UUID")
    full_name: str = Field(description="Ad soyad")
    phone: str | None = Field(default=None, description="Telefon numarası")
    email: str | None = Field(default=None, description="E-posta adresi")
    customer_type: str = Field(description="Müşteri tipi")
    budget_min: float | None = Field(default=None, description="Minimum bütçe (TRY)")
    budget_max: float | None = Field(default=None, description="Maksimum bütçe (TRY)")
    desired_rooms: str | None = Field(default=None, description="Tercih edilen oda sayısı")
    desired_area_min: int | None = Field(default=None, description="Minimum aranan alan (m²)")
    desired_area_max: int | None = Field(default=None, description="Maksimum aranan alan (m²)")
    desired_districts: list[str] = Field(default_factory=list, description="Tercih edilen ilçeler")
    tags: list[str] = Field(default_factory=list, description="Müşteri etiketleri")
    lead_status: str = Field(description="Lead durumu")
    source: str | None = Field(default=None, description="Müşteri kaynağı")
    last_contact_at: datetime | None = Field(default=None, description="Son iletişim zamanı")
    created_at: datetime = Field(description="Oluşturulma zamanı")
    updated_at: datetime = Field(description="Son güncelleme zamanı")


class CustomerListResponse(BaseModel):
    """Müşteri listesi yanıtı (pagination destekli)."""

    items: list[CustomerResponse] = Field(description="Müşteri listesi")
    total: int = Field(description="Toplam müşteri sayısı")
    page: int = Field(description="Mevcut sayfa numarası")
    per_page: int = Field(description="Sayfa başına kayıt sayısı")


# ================================================================
# Note Request/Response Modelleri
# ================================================================


class NoteCreate(BaseModel):
    """Yeni not oluşturma isteği."""

    content: str = Field(
        min_length=1,
        description="Not içeriği",
    )
    note_type: Literal["note", "call", "meeting", "email"] = Field(
        default="note",
        description="Not tipi",
    )


class NoteResponse(BaseModel):
    """Tek not yanıtı."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Not UUID")
    content: str = Field(description="Not içeriği")
    note_type: str = Field(description="Not tipi")
    user_id: str | None = Field(default=None, description="Oluşturan kullanıcı UUID")
    created_at: datetime = Field(description="Oluşturulma zamanı")


class NoteListResponse(BaseModel):
    """Not listesi yanıtı."""

    items: list[NoteResponse] = Field(description="Not listesi")
    total: int = Field(description="Toplam not sayısı")


# ================================================================
# Timeline Modelleri
# ================================================================


class TimelineItem(BaseModel):
    """Tek timeline aktivite öğesi."""

    type: str = Field(description="Aktivite tipi: note, match")
    content: str = Field(description="Aktivite içeriği/açıklaması")
    timestamp: datetime = Field(description="Aktivite zamanı")
    metadata: dict | None = Field(default=None, description="Ek bilgi (opsiyonel)")


class TimelineResponse(BaseModel):
    """Timeline yanıtı (birleşik aktivite akışı)."""

    items: list[TimelineItem] = Field(description="Aktivite listesi")
    total: int = Field(description="Toplam aktivite sayısı")
