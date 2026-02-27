"""
Emlak Teknoloji Platformu - Notification Schemas

Bildirim modulu icin Pydantic veri modelleri.
API request/response serialization.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ================================================================
# Response Modelleri
# ================================================================


class NotificationResponse(BaseModel):
    """Tek bildirim yaniti."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Bildirim UUID")
    type: str = Field(description="Bildirim tipi (new_match, new_message vb.)")
    title: str = Field(description="Bildirim basligi")
    body: str | None = Field(default=None, description="Bildirim detay metni")
    is_read: bool = Field(description="Okundu mu")
    data: dict = Field(default_factory=dict, description="Ek veriler (JSON)")
    created_at: datetime = Field(description="Olusturulma zamani")


class NotificationListResponse(BaseModel):
    """Bildirim listesi yaniti (pagination destekli)."""

    items: list[NotificationResponse] = Field(description="Bildirim listesi")
    total: int = Field(description="Toplam bildirim sayisi")


class UnreadCountResponse(BaseModel):
    """Okunmamis bildirim sayisi yaniti."""

    count: int = Field(description="Okunmamis bildirim sayisi")
