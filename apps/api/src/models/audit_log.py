"""
Emlak Teknoloji Platformu - AuditLog Model

KVKK uyumlu denetim kayitlari. Tum kullanici eylemlerini kayit altina alir.
Veri degisiklikleri (old_value/new_value), erisim bilgileri (IP, user agent)
ve etkilenen entity bilgileri saklanir.

KVKK Audit Bulgusu #3: Denetim izi eksikligi giderildi.
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import BaseModel, TenantMixin


class AuditAction(enum.StrEnum):
    """Denetlenen eylem tipleri."""

    CREATE = "CREATE"
    READ = "READ"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    EXPORT = "EXPORT"


class AuditLog(BaseModel, TenantMixin):
    """
    KVKK Denetim Kaydi.

    Immutable: Olusturulduktan sonra guncellenemez veya silinemez.
    Saklama suresi: KVKK geregince minimum 2 yil.

    Ornek kullanim:
        - Musteri verisi guncelleme → action=UPDATE, entity_type=Customer
        - Kullanici girisi → action=LOGIN, entity_type=User
        - Degerleme raporu export → action=EXPORT, entity_type=PredictionLog
    """

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("ix_audit_logs_office_id", "office_id"),
        Index("ix_audit_logs_user_id", "user_id"),
        Index("ix_audit_logs_entity_type_entity_id", "entity_type", "entity_id"),
        Index("ix_audit_logs_action", "action"),
        Index("ix_audit_logs_created_at", "created_at"),
        # Composite: tenant + tarih bazli sorgular (KVKK raporlama)
        Index("ix_audit_logs_office_created", "office_id", "created_at"),
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bagli ofis (tenant) ID",
    )

    # ---------- Kullanici ----------
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Eylemi gerceklestiren kullanici ID",
    )

    # ---------- Eylem Bilgileri ----------
    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Eylem tipi: CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, EXPORT",
    )

    # ---------- Etkilenen Entity ----------
    entity_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Etkilenen varlik tipi (model adi: Customer, Property, vb.)",
    )
    entity_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
        comment="Etkilenen varlik UUID (login/logout gibi entity-siz eylemler icin null)",
    )

    # ---------- Veri Degisiklikleri (KVKK Maddesi: Veri isleme izlenebilirlik) ----------
    old_value: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Degisiklik oncesi degerler (UPDATE/DELETE icin)",
    )
    new_value: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Degisiklik sonrasi degerler (CREATE/UPDATE icin)",
    )

    # ---------- Erisim Bilgileri (KVKK Maddesi: Kim, ne zaman, nereden) ----------
    ip_address: Mapped[str | None] = mapped_column(
        String(45),
        nullable=True,
        comment="Istemci IP adresi (IPv4/IPv6)",
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        comment="Istemci user agent bilgisi",
    )
