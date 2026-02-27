"""
Emlak Teknoloji Platformu - Outbox Event Model

Transactional Outbox pattern: Domain event'leri aynı transaction içinde
outbox tablosuna yazılır, ardından worker tarafından asenkron işlenir.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TenantMixin


class OutboxEvent(BaseModel, TenantMixin):
    """
    Outbox event kaydı.

    Durumlar (status): pending, processing, sent, failed, dead_letter
    Worker tarafından poll edilir ve işlenir (FOR UPDATE SKIP LOCKED).
    """

    __tablename__ = "outbox_events"
    __table_args__ = (
        Index("ix_outbox_status_next_retry", "status", "next_retry_at"),
        Index("ix_outbox_aggregate", "aggregate_type", "aggregate_id"),
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı ofis (tenant) ID",
    )

    # ---------- Event Bilgileri ----------
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Event tipi (ör: property.created, payment.completed)",
    )
    aggregate_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Aggregate tipi (ör: Property, Payment)",
    )
    aggregate_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        comment="Aggregate entity ID",
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
        default="pending",
        server_default=text("'pending'"),
        comment="Event durumu: pending, processing, sent, failed, dead_letter",
    )
    locked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Worker tarafından kilitlenme zamanı",
    )
    locked_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Kilitleyen worker ID",
    )
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="İşlenme zamanı",
    )

    # ---------- Retry ----------
    retry_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Tekrar deneme sayısı",
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        server_default=text("5"),
        comment="Maksimum tekrar deneme sayısı",
    )
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Sonraki tekrar deneme zamanı",
    )
    error_message: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        comment="Son hata mesajı",
    )

    # ---------- İlişkiler ----------
    office = relationship("Office", lazy="selectin")
