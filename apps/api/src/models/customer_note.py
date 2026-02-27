"""
Emlak Teknoloji Platformu - CustomerNote Model

Müşteri notları entity'si — ofis bazlı multi-tenant.
Not tipleri: note, call, meeting, email.
"""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TenantMixin


class CustomerNote(BaseModel, TenantMixin):
    """
    Müşteri notu — CRM aktivite kaydı.

    Her not bir müşteriye aittir ve bir ofis altında tutulur (multi-tenant).
    Notu oluşturan kullanıcı (user_id) opsiyoneldir (silinmiş kullanıcı durumu).

    Not tipleri:
        - note: Genel not
        - call: Telefon görüşmesi
        - meeting: Toplantı / randevu
        - email: E-posta iletişimi
    """

    __tablename__ = "customer_notes"
    __table_args__ = (
        Index("ix_customer_notes_customer_id", "customer_id"),
        Index("ix_customer_notes_office_id", "office_id"),
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı ofis (tenant) ID",
    )

    # ---------- Müşteri ----------
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        comment="İlişkili müşteri ID",
    )

    # ---------- Oluşturan Kullanıcı ----------
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Notu oluşturan kullanıcı ID (silinirse NULL)",
    )

    # ---------- İçerik ----------
    content: Mapped[str] = mapped_column(
        Text, nullable=False,
        comment="Not içeriği",
    )

    note_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="note",
        server_default=text("'note'"),
        comment="Not tipi: note, call, meeting, email",
    )

    # ---------- İlişkiler ----------
    customer = relationship("Customer", lazy="selectin")
    user = relationship("User", lazy="selectin")
    office = relationship("Office", lazy="selectin")
