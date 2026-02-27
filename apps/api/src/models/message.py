"""
Emlak Teknoloji Platformu - Conversation & Message Models

Omnichannel mesajlaşma modelleri (Telegram, WhatsApp, Web).
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TenantMixin


class Conversation(BaseModel, TenantMixin):
    """
    Müşteri ile ofis arasındaki konuşma.

    Her konuşma bir müşteriye ve bir ofise bağlıdır.
    Kanal (Telegram, WhatsApp, Web) bazında ayrışır.
    """

    __tablename__ = "conversations"
    __table_args__ = (
        Index("ix_conversations_office_id", "office_id"),
        Index("ix_conversations_customer_id", "customer_id"),
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
        ForeignKey("customers.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı müşteri ID",
    )

    # ---------- Kanal ----------
    channel: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="İletişim kanalı: telegram, whatsapp, web",
    )

    # ---------- Durum ----------
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="open",
        server_default=text("'open'"),
        comment="Konuşma durumu: open, closed, archived",
    )

    last_message_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Son mesaj zamanı",
    )

    # ---------- İlişkiler ----------
    office = relationship("Office", lazy="selectin")
    customer = relationship("Customer", lazy="selectin")
    messages: Mapped[list[Message]] = relationship(
        "Message", back_populates="conversation", lazy="raise",
        order_by="Message.created_at",
    )


class Message(BaseModel, TenantMixin):
    """
    Tek bir mesaj kaydı.

    Konuşma içindeki her bir mesajın yönü (inbound/outbound),
    içeriği, tipi ve durumu tutulur.

    office_id denormalize edilmiştir (conversations.office_id kopyası).
    RLS (Row-Level Security) policy'leri doğrudan bu alan üzerinden çalışır.
    """

    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_created", "conversation_id", "created_at"),
        Index("ix_messages_office_id", "office_id"),
    )

    # ---------- Tenant (denormalize — RLS için zorunlu) ----------
    office_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id"),
        nullable=True,
        comment="Denormalize ofis ID (RLS için). Conversation'dan kopyalanır.",
    )

    # ---------- Konuşma ----------
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        comment="Bağlı konuşma ID",
    )

    # ---------- İçerik ----------
    direction: Mapped[str] = mapped_column(
        String(10), nullable=False,
        comment="Mesaj yönü: inbound (müşteriden), outbound (ofisten)",
    )
    content: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Mesaj metni"
    )
    message_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="text",
        server_default=text("'text'"),
        comment="Mesaj tipi: text, image, document, location",
    )
    channel: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="Kanal: telegram, whatsapp, web",
    )

    # ---------- Durum ----------
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="sent",
        server_default=text("'sent'"),
        comment="Mesaj durumu: sent, delivered, read, failed",
    )

    # ---------- Harici Referans ----------
    external_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True,
        comment="Harici platform mesaj ID (Telegram message_id vb.)",
    )

    # ---------- İlişkiler ----------
    office = relationship("Office", lazy="selectin")
    conversation: Mapped[Conversation] = relationship(
        "Conversation", back_populates="messages", lazy="selectin",
    )
