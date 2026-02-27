"""
Emlak Teknoloji Platformu - Showcase Model

Danışman Portfolyo Vitrini — danışmanların seçili ilanlarını
public bir URL üzerinden sergileyebildiği vitrin sayfası.
"""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TenantMixin


class Showcase(BaseModel, TenantMixin):
    """
    Danışman Portfolyo Vitrini.

    Her danışman bir veya daha fazla vitrin oluşturabilir.
    Vitrin, seçili ilanları public bir slug URL'de sergiler.
    Tema, iletişim bilgileri ve görüntülenme istatistikleri içerir.
    """

    __tablename__ = "showcases"
    __table_args__ = (
        # Composite B-tree: ofis + danışman bazlı sorgular
        Index("ix_showcases_office_agent", "office_id", "agent_id"),
        # Partial index: sadece aktif vitrinler (en sık sorgu)
        Index(
            "ix_showcases_is_active",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı ofis (tenant) ID",
    )

    # ---------- Danışman (vitrin sahibi) ----------
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Vitrin sahibi danışman ID",
    )

    # ---------- Vitrin Bilgileri ----------
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Vitrin başlığı"
    )
    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Public URL slug (ör: ali-yilmaz-kadikoy)",
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Vitrin açıklaması"
    )

    # ---------- Seçili İlanlar ----------
    selected_properties: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb"),
        comment="Seçili ilan UUID listesi (JSON array)",
    )

    # ---------- Danışman İletişim ----------
    agent_photo_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Danışman profil fotoğrafı URL"
    )
    agent_phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Danışman telefon numarası"
    )
    agent_email: Mapped[str | None] = mapped_column(
        String(200), nullable=True, comment="Danışman e-posta adresi"
    )
    agent_whatsapp: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Danışman WhatsApp numarası"
    )

    # ---------- Tema & Ayarlar ----------
    theme: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="default",
        server_default=text("'default'"),
        comment="Vitrin teması: default, modern, classic vb.",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        comment="Vitrin aktif mi",
    )
    settings: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="Ek vitrin ayarları (JSON)",
    )

    # ---------- İstatistik ----------
    views_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Görüntülenme sayısı",
    )

    # ---------- İlişkiler ----------
    office = relationship("Office", lazy="selectin")
    agent = relationship("User", lazy="selectin")
