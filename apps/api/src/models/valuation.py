"""
Emlak Teknoloji Platformu - PropertyValuation Model

Emlak degerleme kaydi. Her degerleme bir ofis ve kullaniciya aittir,
opsiyonel olarak bir Property'ye baglaniyor olabilir.
Immutable kayittir — olusturulduktan sonra guncellenmez.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class PropertyValuation(Base):
    """
    Emlak degerleme sonucu.

    ML modeli tarafindan uretilen fiyat tahmini, emsal verileri ve
    guven skoru. Multi-tenant: her degerleme bir office'e aittir.
    """

    __tablename__ = "property_valuations"
    __table_args__ = (
        Index("ix_valuations_office", "office_id"),
        Index("ix_valuations_user", "user_id"),
        Index("ix_valuations_property", "property_id"),
        Index("ix_valuations_city_district", "city", "district"),
        Index("ix_valuations_created", "created_at"),
    )

    # ---------- Primary Key ----------
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # ---------- Multi-tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bagli ofis (tenant) ID",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Degerleme yapan kullanici ID",
    )

    # ---------- Opsiyonel bagli mulk ----------
    property_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id", ondelete="SET NULL"),
        nullable=True,
        comment="Bagli mulk ID (opsiyonel)",
    )

    # ---------- Degerleme adresi ve konum ----------
    address: Mapped[str] = mapped_column(
        Text, nullable=False, comment="Acik adres",
    )
    location = mapped_column(
        Geography("POINT", srid=4326, spatial_index=True),
        nullable=False,
        comment="Konum koordinatlari (GEOGRAPHY POINT)",
    )
    city: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Il",
    )
    district: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="Ilce",
    )
    neighborhood: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Mahalle",
    )

    # ---------- Girdi parametreleri ----------
    input_params: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        comment="Degerleme girdi parametreleri JSON",
    )

    # ---------- Tahmin sonuclari ----------
    estimated_price_min: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False,
        comment="Tahmini minimum fiyat (TL)",
    )
    estimated_price_max: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False,
        comment="Tahmini maksimum fiyat (TL)",
    )
    estimated_price_avg: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False,
        comment="Tahmini ortalama fiyat (TL)",
    )
    confidence_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 4), nullable=False,
        comment="Guven skoru 0.0000 - 1.0000",
    )

    # ---------- Model bilgisi ----------
    model_version: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="ML model versiyon bilgisi",
    )

    # ---------- Emsal veriler ----------
    comparables: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        server_default=text("'[]'::jsonb"),
        comment="Emsal verileri JSON listesi",
    )

    # ---------- Fiyat metrikleri ----------
    price_per_sqm: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True,
        comment="Metrekare birim fiyat (TL/m2)",
    )
    area_avg_price_per_sqm: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2), nullable=True,
        comment="Bolge ortalama metrekare birim fiyat (TL/m2)",
    )

    # ---------- Rapor ----------
    report_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        comment="Degerleme raporu URL",
    )

    # ---------- Zaman ----------
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # ---------- Iliskiler ----------
    office = relationship("Office", lazy="selectin")
    user = relationship("User", lazy="selectin")
    property = relationship("Property", lazy="selectin")
