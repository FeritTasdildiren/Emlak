"""
Emlak Teknoloji Platformu - UsageQuota Model

Aylık değerleme kota takibi.
Her ofis, abonelik planına göre aylık belirli sayıda değerleme yapabilir.

Plan limitleri:
    - Starter : 10 değerleme/ay
    - Pro     : 100 değerleme/ay
    - Elite   : 9999 değerleme/ay (pratik olarak sınırsız)
"""

import uuid
from datetime import date

from sqlalchemy import (
    Date,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TenantMixin


class UsageQuota(TenantMixin, BaseModel):
    """Aylık değerleme kota takibi."""

    __tablename__ = "usage_quotas"
    __table_args__ = (
        UniqueConstraint(
            "office_id",
            "period_start",
            name="uq_usage_quotas_office_period",
        ),
        Index("ix_usage_quotas_office_id", "office_id"),
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı ofis (tenant) ID",
    )

    # ---------- Dönem ----------
    period_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Kota dönem başlangıcı (ayın ilk günü)",
    )
    period_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Kota dönem bitişi (ayın son günü)",
    )

    # ---------- Kullanım ----------
    valuations_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Bu dönemde yapılan değerleme sayısı",
    )
    valuations_limit: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="Plan bazlı aylık değerleme limiti",
    )

    # ---------- Yeni Sayaçlar (018_usage_quota_expand) ----------
    listings_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Bu dönemde oluşturulan ilan sayısı",
    )
    staging_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Bu dönemde yapılan sahneleme sayısı",
    )
    photos_used: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Bu dönemde yüklenen fotoğraf sayısı",
    )
    credit_balance: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default=text("0"),
        comment="Ekstra kredi bakiyesi (kota aşımında kullanılır)",
    )

    # ---------- İlişkiler ----------
    office = relationship("Office", lazy="selectin")
