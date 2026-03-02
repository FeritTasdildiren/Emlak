"""
Emlak Teknoloji Platformu - Appointment Schemas

Randevu modülü için Pydantic veri modelleri.
API request/response serialization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ================================================================
# Request Modelleri
# ================================================================


class AppointmentCreate(BaseModel):
    """Yeni randevu oluşturma isteği."""

    title: str = Field(
        min_length=2, max_length=200,
        description="Randevu başlığı",
    )
    appointment_date: datetime = Field(
        description="Randevu tarihi ve saati (ISO 8601)",
    )
    duration_minutes: int = Field(
        default=30, ge=5, le=480,
        description="Randevu süresi (dakika, 5-480)",
    )
    status: Literal["scheduled", "completed", "cancelled", "no_show"] = Field(
        default="scheduled",
        description="Randevu durumu",
    )
    customer_id: str | None = Field(
        default=None,
        description="Bağlı müşteri UUID (opsiyonel)",
    )
    property_id: str | None = Field(
        default=None,
        description="Bağlı ilan UUID (opsiyonel)",
    )
    description: str | None = Field(
        default=None,
        description="Ek açıklama",
    )
    location: str | None = Field(
        default=None, max_length=300,
        description="Randevu yeri",
    )
    notes: str | None = Field(
        default=None,
        description="Dahili notlar",
    )


class AppointmentUpdate(BaseModel):
    """Randevu güncelleme isteği. Sadece gönderilen alanlar güncellenir."""

    title: str | None = Field(
        default=None, min_length=2, max_length=200,
        description="Randevu başlığı",
    )
    appointment_date: datetime | None = Field(
        default=None,
        description="Randevu tarihi ve saati (ISO 8601)",
    )
    duration_minutes: int | None = Field(
        default=None, ge=5, le=480,
        description="Randevu süresi (dakika, 5-480)",
    )
    status: Literal["scheduled", "completed", "cancelled", "no_show"] | None = Field(
        default=None,
        description="Randevu durumu",
    )
    customer_id: str | None = Field(
        default=None,
        description="Bağlı müşteri UUID",
    )
    property_id: str | None = Field(
        default=None,
        description="Bağlı ilan UUID",
    )
    description: str | None = Field(
        default=None,
        description="Ek açıklama",
    )
    location: str | None = Field(
        default=None, max_length=300,
        description="Randevu yeri",
    )
    notes: str | None = Field(
        default=None,
        description="Dahili notlar",
    )


# ================================================================
# Response Modelleri
# ================================================================


class AppointmentResponse(BaseModel):
    """Tek randevu yanıtı."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Randevu UUID")
    title: str = Field(description="Randevu başlığı")
    description: str | None = Field(default=None, description="Ek açıklama")
    appointment_date: datetime = Field(description="Randevu tarihi ve saati")
    duration_minutes: int = Field(description="Randevu süresi (dakika)")
    status: str = Field(description="Randevu durumu")
    location: str | None = Field(default=None, description="Randevu yeri")
    notes: str | None = Field(default=None, description="Dahili notlar")
    customer_id: str | None = Field(default=None, description="Bağlı müşteri UUID")
    property_id: str | None = Field(default=None, description="Bağlı ilan UUID")
    user_id: str = Field(description="Danışman UUID")
    user_name: str = Field(description="Danışman adı")
    customer_name: str | None = Field(default=None, description="Müşteri adı")
    property_title: str | None = Field(default=None, description="İlan başlığı")
    created_at: datetime = Field(description="Oluşturulma zamanı")
    updated_at: datetime = Field(description="Son güncelleme zamanı")


class AppointmentListResponse(BaseModel):
    """Randevu listesi yanıtı (pagination destekli)."""

    items: list[AppointmentResponse] = Field(description="Randevu listesi")
    total: int = Field(description="Toplam randevu sayısı")
    skip: int = Field(description="Atlanan kayıt sayısı")
    limit: int = Field(description="Sayfa başına kayıt limiti")
