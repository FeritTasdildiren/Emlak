"""
Emlak Teknoloji Platformu - Audit Schemas

KVKK denetim kayitlari icin Pydantic veri modelleri.
API request/response serialization.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from datetime import datetime

# ================================================================
# Response Modelleri
# ================================================================


class AuditLogResponse(BaseModel):
    """Tek audit log kaydi yaniti."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Audit log UUID")
    user_id: str = Field(description="Eylemi gerceklestiren kullanici UUID")
    office_id: str = Field(description="Ofis (tenant) UUID")
    action: str = Field(
        description="Eylem tipi: CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, EXPORT",
    )
    entity_type: str = Field(description="Etkilenen varlik tipi")
    entity_id: str | None = Field(
        default=None,
        description="Etkilenen varlik UUID",
    )
    old_value: dict | None = Field(
        default=None,
        description="Degisiklik oncesi degerler",
    )
    new_value: dict | None = Field(
        default=None,
        description="Degisiklik sonrasi degerler",
    )
    ip_address: str | None = Field(
        default=None,
        description="Istemci IP adresi",
    )
    user_agent: str | None = Field(
        default=None,
        description="Istemci user agent",
    )
    created_at: datetime = Field(description="Kayit olusturulma zamani")


class AuditLogListResponse(BaseModel):
    """Audit log listesi yaniti (pagination destekli)."""

    items: list[AuditLogResponse] = Field(description="Audit log listesi")
    total: int = Field(description="Toplam kayit sayisi")
    page: int = Field(description="Mevcut sayfa numarasi")
    per_page: int = Field(description="Sayfa basina kayit sayisi")


# ================================================================
# Query Modelleri (filtre parametreleri)
# ================================================================


# Literal type tanimlari endpoint Query parametrelerinde kullanilir.
# Dogrudan Literal olarak export edilir — ayri bir schema class'i gerekmez.
AuditActionFilter = Literal[
    "CREATE", "READ", "UPDATE", "DELETE", "LOGIN", "LOGOUT", "EXPORT"
]
