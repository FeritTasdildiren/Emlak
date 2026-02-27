"""
Emlak Teknoloji Platformu - Match Schemas

İlan-Müşteri eşleştirme modülü için Pydantic veri modelleri.
API request/response serialization.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

# ================================================================
# Request Modelleri
# ================================================================


class MatchStatusUpdate(BaseModel):
    """Eşleştirme status güncelleme isteği."""

    status: Literal["pending", "interested", "passed", "contacted", "converted"] = Field(
        description="Yeni eşleştirme durumu",
    )
    notes: str | None = Field(
        default=None,
        description="Opsiyonel not",
    )


# ================================================================
# Response Modelleri
# ================================================================


class MatchResponse(BaseModel):
    """Tek eşleştirme yanıtı."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Eşleştirme UUID")
    property_id: str = Field(description="İlan UUID")
    customer_id: str = Field(description="Müşteri UUID")
    score: float = Field(description="Eşleşme skoru (0-100)")
    status: str = Field(description="Eşleştirme durumu")
    matched_at: datetime = Field(description="Eşleştirme zamanı")
    responded_at: datetime | None = Field(default=None, description="Yanıt zamanı")
    notes: str | None = Field(default=None, description="Notlar")
    created_at: datetime = Field(description="Oluşturulma zamanı")
    updated_at: datetime = Field(description="Son güncelleme zamanı")


class MatchListResponse(BaseModel):
    """Eşleştirme listesi yanıtı (pagination destekli)."""

    items: list[MatchResponse] = Field(description="Eşleştirme listesi")
    total: int = Field(description="Toplam eşleştirme sayısı")
    page: int = Field(description="Mevcut sayfa numarası")
    per_page: int = Field(description="Sayfa başına kayıt sayısı")


class MatchRunResponse(BaseModel):
    """Eşleştirme çalıştırma (run) yanıtı."""

    matches_found: int = Field(description="Eşik üstü eşleşme sayısı")
    matches_created: int = Field(description="Oluşturulan/güncellenen eşleşme sayısı")
    top_score: float | None = Field(default=None, description="En yüksek skor")
    execution_time_ms: int = Field(description="Çalışma süresi (ms)")
