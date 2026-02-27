"""
Emlak Teknoloji Platformu - User Model

Platform kullanıcısı (emlak danışmanı, ofis yöneticisi vb.)
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Index, String, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TenantMixin

if TYPE_CHECKING:
    from src.models.office import Office


class User(BaseModel, TenantMixin):
    """
    Platform kullanıcısı.

    Roller:
    - agent: Emlak danışmanı
    - office_admin: Ofis yöneticisi
    - office_owner: Ofis sahibi
    - platform_admin: Platform yöneticisi
    """

    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_office_id", "office_id"),
        Index("ix_users_email", "email", unique=True),
        Index("ix_users_telegram_id", "telegram_id", unique=True, postgresql_where=text("telegram_id IS NOT NULL")),
        Index("ix_users_telegram_chat_id", "telegram_chat_id", unique=True, postgresql_where=text("telegram_chat_id IS NOT NULL")),
    )

    # ---------- Kimlik ----------
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, comment="E-posta adresi"
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Telefon numarası"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Bcrypt hash'lenmiş şifre"
    )
    full_name: Mapped[str] = mapped_column(
        String(150), nullable=False, comment="Ad soyad"
    )
    avatar_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Profil fotoğrafı URL'i"
    )

    # ---------- Rol ----------
    role: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="Kullanıcı rolü: agent, office_admin, office_owner, platform_admin",
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı ofis (tenant) ID",
    )

    # ---------- Mesajlaşma Kanalları ----------
    telegram_id: Mapped[int | None] = mapped_column(
        BigInteger, unique=True, nullable=True, comment="Telegram kullanıcı ID"
    )
    telegram_chat_id: Mapped[str | None] = mapped_column(
        String(50), unique=True, nullable=True,
        comment="Telegram bot chat ID (deep link ile baglanan)",
    )
    whatsapp_phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="WhatsApp telefon numarası"
    )
    preferred_channel: Mapped[str] = mapped_column(
        String(20), nullable=False, default="telegram",
        server_default=text("'telegram'"),
        comment="Tercih edilen iletişim kanalı",
    )

    # ---------- Durum ----------
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true"),
        comment="Hesap aktif mi",
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false"),
        comment="E-posta doğrulanmış mı",
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Son giriş zamanı"
    )

    # ---------- İlişkiler ----------
    office: Mapped[Office] = relationship(
        "Office", back_populates="users", lazy="selectin",
    )
