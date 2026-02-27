"""
Emlak Teknoloji Platformu - Inbox Event Model

Inbox pattern: Gelen event'lerin idempotent işlenmesini sağlar.
event_id UNIQUE constraint ile duplicate event'ler engellenir.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel


class InboxEvent(BaseModel):
    """
    Inbox event kaydı.

    Durumlar (status): received, processing, processed, failed
    event_id UNIQUE constraint duplicate event işlemeyi engeller.
    """

    __tablename__ = "inbox_events"

    # ---------- Tenant (NULLABLE) ----------
    office_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Bağlı ofis (tenant) ID — platform-level event'ler için NULL",
    )

    # ---------- Event Bilgileri ----------
    event_id: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        comment="Kaynak sistemdeki benzersiz event ID (idempotency key)",
    )
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Event kaynağı (ör: payment-gateway, notification-service)",
    )
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Event tipi (ör: payment.webhook, sms.delivery_report)",
    )
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="Event payload (JSON)",
    )

    # ---------- İşleme Durumu ----------
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="received",
        server_default=text("'received'"),
        comment="Event durumu: received, processing, processed, failed",
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="İşlenme zamanı",
    )
    error_message: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        comment="Hata mesajı",
    )

    # ---------- İlişkiler ----------
    office = relationship("Office", lazy="selectin")
