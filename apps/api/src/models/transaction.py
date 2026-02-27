"""
Emlak Teknoloji Platformu - Transaction Model

Odeme islem kayitlari. Her transaction bir payment'a baglidir.
Charge, refund, void ve adjustment islem tiplerini destekler.

KVKK Audit Bulgusu #2: Odeme takibi eksikligi giderildi.
"""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TenantMixin


class TransactionType(enum.StrEnum):
    """Islem tipi."""

    CHARGE = "charge"
    REFUND = "refund"
    VOID = "void"
    ADJUSTMENT = "adjustment"


class TransactionStatus(enum.StrEnum):
    """Islem durumu."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class Transaction(BaseModel, TenantMixin):
    """
    Odeme islemi kaydi.

    Her odeme (Payment) birden fazla transaction'a sahip olabilir.
    Ornek: Bir odeme basarili (CHARGE/COMPLETED) olduktan sonra
    kismi iade (REFUND/COMPLETED) yapilabilir.
    """

    __tablename__ = "transactions"
    __table_args__ = (
        Index("ix_transactions_office_id", "office_id"),
        Index("ix_transactions_payment_id", "payment_id"),
        Index(
            "ix_transactions_external_transaction_id",
            "external_transaction_id",
            unique=True,
            postgresql_where=text("external_transaction_id IS NOT NULL"),
        ),
        Index("ix_transactions_status", "status"),
        Index("ix_transactions_type", "type"),
        Index("ix_transactions_created_at", "created_at"),
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bagli ofis (tenant) ID",
    )

    # ---------- Payment ----------
    payment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("payments.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bagli odeme ID",
    )

    # ---------- Islem Bilgileri ----------
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Islem tipi: charge, refund, void, adjustment",
    )
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Islem tutari",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        server_default=text("'pending'"),
        comment="Islem durumu: pending, completed, failed",
    )

    # ---------- Harici Saglayici ----------
    external_transaction_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        comment="Odeme saglayici islem ID (duplicate engeli)",
    )

    # ---------- Ek Bilgiler ----------
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="Ek bilgiler JSON (saglayici yanitlari vb.)",
    )
    error_message: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        comment="Basarisiz islem hata mesaji",
    )

    # ---------- Iliskiler ----------
    payment = relationship("Payment", lazy="selectin")
    office = relationship("Office", lazy="selectin")
