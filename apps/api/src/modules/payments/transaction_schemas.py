"""
Emlak Teknoloji Platformu - Transaction Schemas

Odeme islem kayitlari icin Pydantic veri modelleri.
API response serialization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from datetime import datetime

# ================================================================
# Response Modelleri
# ================================================================


class TransactionResponse(BaseModel):
    """Tek transaction yaniti."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Transaction UUID")
    payment_id: str = Field(description="Bagli odeme UUID")
    office_id: str = Field(description="Ofis (tenant) UUID")
    type: str = Field(description="Islem tipi: charge, refund, void, adjustment")
    amount: float = Field(description="Islem tutari")
    status: str = Field(description="Islem durumu: pending, completed, failed")
    external_transaction_id: str | None = Field(
        default=None,
        description="Odeme saglayici islem ID",
    )
    metadata: dict = Field(
        default_factory=dict,
        description="Ek bilgiler JSON",
    )
    error_message: str | None = Field(
        default=None,
        description="Hata mesaji (basarisiz islemler icin)",
    )
    created_at: datetime = Field(description="Olusturulma zamani")
    updated_at: datetime = Field(description="Son guncelleme zamani")


class TransactionListResponse(BaseModel):
    """Transaction listesi yaniti (pagination destekli)."""

    items: list[TransactionResponse] = Field(description="Transaction listesi")
    total: int = Field(description="Toplam kayit sayisi")
    page: int = Field(description="Mevcut sayfa numarasi")
    per_page: int = Field(description="Sayfa basina kayit sayisi")
