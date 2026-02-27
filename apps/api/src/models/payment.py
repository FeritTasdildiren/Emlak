"""
Emlak Teknoloji Platformu - Payment Model

Ödeme kayıtları. Her ödeme bir subscription'a ve office'e bağlıdır.
Ödeme sağlayıcı entegrasyonu (iyzico vb.) için external_id alanı UNIQUE'tir
— aynı ödemenin tekrar kaydedilmesini (duplicate) engeller.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TenantMixin


class Payment(BaseModel, TenantMixin):
    """
    Ödeme kaydı.

    Durumlar (status): pending, processing, completed, failed, refunded
    Ödeme yöntemleri (payment_method): credit_card, bank_transfer, iyzico
    """

    __tablename__ = "payments"
    __table_args__ = (
        Index("ix_payments_office_id", "office_id"),
        Index("ix_payments_subscription_id", "subscription_id"),
        Index("ix_payments_external_id", "external_id", unique=True),
        Index("ix_payments_status", "status"),
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı ofis (tenant) ID",
    )

    # ---------- Subscription ----------
    subscription_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı abonelik ID",
    )

    # ---------- Ödeme Bilgileri ----------
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
        comment="Ödeme tutarı",
    )
    currency: Mapped[str] = mapped_column(
        String(3),
        nullable=False,
        server_default=text("'TRY'"),
        comment="Para birimi (ISO 4217)",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Ödeme durumu: pending, processing, completed, failed, refunded",
    )
    payment_method: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        comment="Ödeme yöntemi: credit_card, bank_transfer, iyzico",
    )

    # ---------- Harici Sağlayıcı ----------
    external_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        unique=True,
        comment="Ödeme sağlayıcı benzersiz ID (duplicate ödeme engeli)",
    )
    external_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Ödeme sağlayıcı durum kodu",
    )

    # ---------- Tarihler ----------
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ödeme tamamlanma zamanı",
    )
    refunded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="İade zamanı",
    )
    initiated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ödeme başlatılma zamanı",
    )
    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ödeme onaylanma zamanı",
    )

    # ---------- İade / Void ----------
    refund_amount: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        comment="İade tutarı (kısmi iade destekler)",
    )
    refund_reason: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="İade nedeni açıklaması",
    )
    void_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ödeme iptal (void) zamanı",
    )

    # ---------- Ek Bilgiler ----------
    # Python'da 'metadata' reserved word olduğu için column_name ile
    # DB'de 'metadata' olarak saklanır, Python'da 'metadata_' olarak erişilir.
    metadata_: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="Ek bilgiler JSON (sağlayıcı yanıtları, kart bilgisi vb.)",
    )
    error_message: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
        comment="Başarısız ödeme hata mesajı",
    )

    # ---------- İlişkiler ----------
    subscription = relationship("Subscription", back_populates="payments")
    office = relationship("Office", lazy="selectin")
