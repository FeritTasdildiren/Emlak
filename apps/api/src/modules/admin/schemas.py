"""
Emlak Teknoloji Platformu - Admin Module Schemas

Admin endpoint'leri icin Pydantic response/request semalari.
DLQ (Dead Letter Queue) yonetim endpoint'leri icin modeller.

Referans: TASK-041
"""

from __future__ import annotations

from pydantic import BaseModel, Field

# ---------- Dead Letter Event ----------


class DeadLetterResponse(BaseModel):
    """Tek bir dead letter event'in detay yaniti."""

    id: str = Field(description="Event UUID")
    office_id: str = Field(description="Tenant (ofis) UUID")
    event_type: str = Field(description="Event tipi (or: payment.completed)")
    aggregate_type: str = Field(description="Aggregate tipi (or: Property, Payment)")
    aggregate_id: str = Field(description="Aggregate entity UUID")
    payload: dict = Field(description="Event payload (JSON)")
    status: str = Field(description="Event durumu (dead_letter)")
    retry_count: int = Field(description="Toplam deneme sayisi")
    max_retries: int = Field(description="Maksimum deneme sayisi")
    error_message: str | None = Field(description="Son hata mesaji")
    created_at: str | None = Field(description="Olusturulma zamani (ISO 8601)")
    updated_at: str | None = Field(description="Son guncelleme zamani (ISO 8601)")

    model_config = {"json_schema_extra": {
        "example": {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "office_id": "123e4567-e89b-12d3-a456-426614174000",
            "event_type": "payment.completed",
            "aggregate_type": "Payment",
            "aggregate_id": "987fcdeb-51a2-3e4f-b678-426614174999",
            "payload": {"amount": 1500, "currency": "TRY"},
            "status": "dead_letter",
            "retry_count": 10,
            "max_retries": 10,
            "error_message": "ConnectionError: payment gateway timeout",
            "created_at": "2026-02-20T14:30:00+03:00",
            "updated_at": "2026-02-20T15:45:00+03:00",
        }
    }}


class DeadLetterListResponse(BaseModel):
    """Dead letter event listesi yaniti (paginasyonlu)."""

    items: list[DeadLetterResponse] = Field(description="Dead letter event listesi")
    total: int = Field(description="Toplam dead letter event sayisi")
    limit: int = Field(description="Sayfa basina kayit sayisi")
    offset: int = Field(description="Baslangic noktasi")


# ---------- Count ----------


class DeadLetterCountResponse(BaseModel):
    """Dead letter event sayisi yaniti."""

    total: int = Field(description="Toplam dead letter sayisi")
    by_event_type: dict[str, int] = Field(
        description="Event tipi bazinda dagilim",
        default_factory=dict,
    )

    model_config = {"json_schema_extra": {
        "example": {
            "total": 15,
            "by_event_type": {
                "payment.completed": 8,
                "notification.send": 4,
                "telegram.message": 3,
            },
        }
    }}


# ---------- Retry ----------


class RetryResponse(BaseModel):
    """Tek event retry yaniti."""

    success: bool = Field(description="Retry basarili mi")
    event_id: str = Field(description="Retry edilen event UUID")
    message: str = Field(description="Sonuc mesaji")


class RetryAllResponse(BaseModel):
    """Toplu retry yaniti."""

    success: bool = Field(description="Islem basarili mi")
    retried_count: int = Field(description="Retry'a gonderilen event sayisi")
    message: str = Field(description="Sonuc mesaji")


# ---------- Purge ----------


class PurgeResponse(BaseModel):
    """DLQ temizleme yaniti."""

    success: bool = Field(description="Islem basarili mi")
    purged_count: int = Field(description="Silinen event sayisi")
    older_than_hours: int = Field(description="Silme esigi (saat)")
    message: str = Field(description="Sonuc mesaji")
