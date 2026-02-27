"""
Emlak Teknoloji Platformu - Notification Model

Kullanıcıya yönelik bildirim entity'si.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, SoftDeleteMixin, TenantMixin


class Notification(BaseModel, TenantMixin, SoftDeleteMixin):
    """
    Kullanıcı bildirimi.

    Yeni ilan eşleşmesi, mesaj geldi, abonelik güncelleme vb.
    bildirimleri kullanıcıya iletir.
    """

    __tablename__ = "notifications"
    __table_args__ = (
        Index("ix_notifications_user_id_is_read", "user_id", "is_read"),
        Index("ix_notifications_office_id", "office_id"),
    )

    # ---------- Kullanıcı ----------
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Hedef kullanıcı ID",
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı ofis (tenant) ID",
    )

    # ---------- İçerik ----------
    type: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Bildirim tipi: new_match, new_message, subscription_update vb.",
    )
    title: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Bildirim başlığı"
    )
    body: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Bildirim detay metni"
    )

    # ---------- Durum ----------
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false"),
        comment="Okundu mu",
    )

    # ---------- Ek Veri ----------
    data: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb"),
        comment="Bildirime ait ek veriler (JSON)",
    )

    # ---------- İlişkiler ----------
    user = relationship("User", lazy="selectin")
    office = relationship("Office", lazy="selectin")
