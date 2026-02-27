"""
Emlak Teknoloji Platformu - Area Analysis Model

Bölge analiz verileri: fiyat ortalamaları, demografik bilgiler, POI skorları.
Platform-level tablo — tenant-specific DEĞİL (office_id YOK).

ADR-0006: Provenance alanları ile veri kaynağı izleme.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import (
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class AreaAnalysis(Base):
    """
    Bölge analiz modeli — şehir/ilçe/mahalle bazında piyasa verileri.

    PostGIS GEOGRAPHY tipi ile polygon sınır bilgisi tutulur.
    JSONB alanlarında demografik ve POI verileri saklanır.
    Provenance alanları ADR-0006 kapsamında veri kaynağı izleme sağlar.
    """

    __tablename__ = "area_analyses"

    # ─── Primary Key ───────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # ─── Bölge Bilgileri ───────────────────────────────────────────────
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    neighborhood: Mapped[str | None] = mapped_column(String(100), nullable=True)
    boundary = mapped_column(
        Geography("POLYGON", srid=4326),
        nullable=True,
    )

    # ─── Fiyat Verileri ───────────────────────────────────────────────
    avg_price_sqm_sale: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    avg_price_sqm_rent: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    price_trend_6m: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        comment="Son 6 aylık fiyat değişim yüzdesi",
    )

    # ─── Piyasa Verileri ──────────────────────────────────────────────
    supply_demand_ratio: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    listing_count: Mapped[int | None] = mapped_column(Integer)

    # ─── Demografik Veriler ───────────────────────────────────────────
    population: Mapped[int | None] = mapped_column(Integer)
    demographics: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="Yaş dağılımı, eğitim seviyesi, gelir düzeyi",
    )
    median_age: Mapped[Decimal | None] = mapped_column(
        Numeric(4, 1), nullable=True, comment="Medyan yaş"
    )
    age_0_14_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="0-14 yaş yüzdesi"
    )
    age_15_24_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="15-24 yaş yüzdesi"
    )
    age_25_44_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="25-44 yaş yüzdesi"
    )
    age_45_64_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="45-64 yaş yüzdesi"
    )
    age_65_plus_pct: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True, comment="65+ yaş yüzdesi"
    )
    population_density: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Nüfus yoğunluğu (kişi/km²)"
    )
    household_count: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Hane sayısı"
    )
    avg_household_size: Mapped[Decimal | None] = mapped_column(
        Numeric(3, 1), nullable=True, comment="Ortalama hane büyüklüğü"
    )

    # ─── POI ve Skorlar ──────────────────────────────────────────────
    poi_data: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        server_default=text("'{}'::jsonb"),
        comment="Okul, hastane, metro, market mesafe/sayı bilgileri",
    )
    transport_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        comment="Ulaşım skoru 0-100",
    )
    amenity_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        comment="Yaşam kolaylığı skoru 0-100",
    )
    investment_score: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2),
        comment="Yatırım potansiyeli skoru 0-100",
    )
    amortization_years: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 1),
        comment="Amortisman süresi (yıl)",
    )

    # ─── PROVENANCE ALANLARI (ADR-0006) ──────────────────────────────
    data_sources: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
        comment='[{"source": "TUIK", "version": "2024-Q4", "fetched_at": "...", "record_count": 42}]',
    )
    provenance_version: Mapped[str | None] = mapped_column(
        String(50),
        comment="Veri versiyonu (ör: 2024-Q4)",
    )
    refresh_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="fresh",
        server_default=text("'fresh'"),
        comment="fresh | stale | refreshing | failed",
    )
    last_refreshed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
    )
    refresh_error: Mapped[str | None] = mapped_column(
        Text,
        comment="Son refresh hatası mesajı",
    )

    # ─── Zaman Damgaları ─────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=datetime.now,
    )

    # ─── Constraints & Indexes ───────────────────────────────────────
    __table_args__ = (
        UniqueConstraint(
            "city",
            "district",
            "neighborhood",
            name="uq_area_city_district_neighborhood",
        ),
        Index("ix_area_city_district", "city", "district"),
        Index("ix_area_refresh_status", "refresh_status"),
    )

    def __repr__(self) -> str:
        parts = [self.city, self.district]
        if self.neighborhood:
            parts.append(self.neighborhood)
        return f"<AreaAnalysis {'/'.join(parts)} refresh={self.refresh_status}>"
