"""
Emlak Teknoloji Platformu - Appointment Model

Randevu entity'si — ofis bazlı multi-tenant.
Danışman-müşteri-ilan arasındaki randevuları yönetir.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TenantMixin


class Appointment(BaseModel, TenantMixin):
    """
    Randevu — danışman ile müşteri arasındaki görüşme planı.

    Her randevu bir ofise aittir (multi-tenant).
    Opsiyonel olarak bir müşteriye ve/veya ilana bağlanabilir.
    """

    __tablename__ = "appointments"
    __table_args__ = (
        Index("ix_appointments_office_date", "office_id", "appointment_date"),
        Index("ix_appointments_office_status", "office_id", "status"),
        Index("ix_appointments_customer_id", "customer_id"),
        Index("ix_appointments_property_id", "property_id"),
        Index("ix_appointments_user_id", "user_id"),
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı ofis (tenant) ID",
    )

    # ---------- Danışman ----------
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        comment="Randevuyu oluşturan danışman ID",
    )

    # ---------- İlişkili Kayıtlar (Opsiyonel) ----------
    customer_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        comment="Bağlı müşteri ID (opsiyonel)",
    )

    property_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="SET NULL"),
        nullable=True,
        comment="Bağlı ilan ID (opsiyonel)",
    )

    # ---------- Randevu Bilgileri ----------
    title: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="Randevu başlığı"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Ek açıklama"
    )
    appointment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Randevu tarihi ve saati",
    )
    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        server_default=text("30"),
        comment="Randevu süresi (dakika)",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="scheduled",
        server_default=text("'scheduled'"),
        comment="Randevu durumu: scheduled, completed, cancelled, no_show",
    )
    location: Mapped[str | None] = mapped_column(
        String(300), nullable=True, comment="Randevu yeri"
    )
    notes: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Dahili notlar"
    )

    # ---------- İlişkiler ----------
    office = relationship("Office", lazy="selectin")
    user = relationship("User", lazy="selectin")
    customer = relationship("Customer", lazy="selectin")
    property = relationship("Property", lazy="selectin")
