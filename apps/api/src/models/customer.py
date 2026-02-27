"""
Emlak Teknoloji Platformu - Customer Model

Müşteri (alıcı/kiracı/satıcı/ev sahibi) entity'si — ofis bazlı multi-tenant.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TenantMixin


class Customer(BaseModel, TenantMixin):
    """
    Müşteri — potansiyel alıcı, kiracı, satıcı veya ev sahibi.

    Her müşteri bir ofise aittir (multi-tenant).
    Opsiyonel olarak bir danışmana (agent) atanabilir.
    Müşterinin bütçe aralığı ve tercih edilen ilan kriterleri tutulur.
    """

    __tablename__ = "customers"
    __table_args__ = (
        Index("ix_customers_office_id_lead_status", "office_id", "lead_status"),
        Index("ix_customers_agent_id", "agent_id"),
        Index("ix_customers_customer_type", "customer_type"),
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı ofis (tenant) ID",
    )

    # ---------- Danışman ----------
    agent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="Atanan danışman (agent) ID",
    )

    # ---------- Kişisel Bilgiler ----------
    full_name: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Ad soyad"
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Telefon numarası"
    )
    email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="E-posta adresi"
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Danışman notları"
    )

    # ---------- Müşteri Tipi ----------
    customer_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="buyer",
        server_default=text("'buyer'"),
        comment="Müşteri tipi: buyer, seller, renter, landlord",
    )

    # ---------- Bütçe ----------
    budget_min: Mapped[float | None] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Minimum bütçe (TRY)"
    )
    budget_max: Mapped[float | None] = mapped_column(
        Numeric(15, 2), nullable=True, comment="Maksimum bütçe (TRY)"
    )

    # ---------- Tercihler ----------
    preferred_type: Mapped[str | None] = mapped_column(
        String(30), nullable=True, comment="Tercih edilen emlak tipi"
    )
    desired_rooms: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Tercih edilen oda sayısı (ör: 2+1, 3+1)"
    )
    desired_area_min: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Minimum aranan alan (m²)"
    )
    desired_area_max: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Maksimum aranan alan (m²)"
    )
    desired_districts: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb"),
        comment="Tercih edilen ilçeler JSON dizisi",
    )

    # ---------- Etiketler ----------
    tags: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb"),
        comment="Müşteri etiketleri JSON dizisi",
    )

    # ---------- Durum ----------
    lead_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="warm",
        server_default=text("'warm'"),
        comment="Lead durumu: cold, warm, hot, converted, lost",
    )
    source: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Müşteri kaynağı (referans, ilan, vb.)"
    )
    last_contact_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
        comment="Son iletişim zamanı",
    )

    # ---------- İlişkiler ----------
    office = relationship("Office", lazy="selectin")
    agent = relationship("User", lazy="selectin")
