"""
Emlak Teknoloji Platformu - Property-Customer Match Model

İlan-Müşteri eşleştirme entity'si — ofis bazlı multi-tenant.
Score tabanlı eşleştirme ve durum takibi.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TenantMixin


class PropertyCustomerMatch(BaseModel, TenantMixin):
    """
    İlan-Müşteri eşleştirmesi.

    Her eşleştirme bir ilan ve bir müşteri arasında yapılır.
    Score (0-100) eşleşme gücünü belirtir.

    Durumlar (status): pending, interested, passed, contacted, converted
    """

    __tablename__ = "property_customer_matches"
    __table_args__ = (
        UniqueConstraint(
            "property_id", "customer_id",
            name="uq_matches_property_customer",
        ),
        Index("ix_matches_office_id_status", "office_id", "status"),
        Index("ix_matches_customer_id", "customer_id"),
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı ofis (tenant) ID",
    )

    # ---------- Eşleştirme Tarafları ----------
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        comment="Eşleştirilen ilan ID",
    )
    customer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        comment="Eşleştirilen müşteri ID",
    )

    # ---------- Eşleştirme Bilgileri ----------
    score: Mapped[float] = mapped_column(
        Float, nullable=False,
        comment="Eşleşme skoru (0-100)",
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending",
        server_default=text("'pending'"),
        comment="Eşleştirme durumu: pending, interested, passed, contacted, converted",
    )

    # ---------- Tarihler ----------
    matched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=text("now()"),
        comment="Eşleştirme zamanı",
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Müşteri yanıt zamanı",
    )

    # ---------- Notlar ----------
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="Eşleştirme notları",
    )

    # ---------- İlişkiler ----------
    property = relationship("Property", lazy="selectin")
    customer = relationship("Customer", lazy="selectin")
    office = relationship("Office", lazy="selectin")
