"""
Emlak Teknoloji Platformu - Subscription Model

Ofis abonelik planı ve durumu.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TenantMixin


class Subscription(BaseModel, TenantMixin):
    """
    Ofis aboneliği.

    Plan tipleri: starter, pro, elite
    Durumlar: trial, active, past_due, cancelled
    """

    __tablename__ = "subscriptions"
    __table_args__ = (
        Index("ix_subscriptions_office_id", "office_id"),
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı ofis (tenant) ID",
    )

    # ---------- Plan ----------
    plan_type: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="Plan tipi: starter, pro, elite",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False,
        comment="Abonelik durumu: trial, active, past_due, cancelled",
    )

    # ---------- Tarihler ----------
    start_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, comment="Başlangıç tarihi"
    )
    end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Bitiş tarihi"
    )
    trial_end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="Deneme süresi bitiş tarihi"
    )

    # ---------- Ücretlendirme ----------
    monthly_price: Mapped[float] = mapped_column(
        Numeric(10, 2), nullable=False, comment="Aylık ücret (TRY)"
    )

    # ---------- Özellikler ----------
    features: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb"),
        comment="Plan özellikleri JSON",
    )

    # ---------- Ödeme Takibi ----------
    last_payment_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Son başarılı ödeme zamanı",
    )
    next_payment_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Sonraki ödeme tarihi",
    )
    payment_failed_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Ardışık başarısız ödeme sayısı",
    )

    # ---------- İlişkiler ----------
    office = relationship("Office", lazy="selectin")
    payments = relationship("Payment", back_populates="subscription", lazy="selectin")
