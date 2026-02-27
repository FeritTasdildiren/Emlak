"""
Emlak Teknoloji Platformu - Deprem Risk Model

Konum bazlı deprem risk verileri: PGA, zemin sınıfı, fay mesafesi, risk skoru.
Platform-level tablo — tenant-specific DEĞİL (office_id YOK).

ADR-0006: Provenance alanları ile veri kaynağı izleme.
PostGIS GEOGRAPHY tipi kullanılır (GEOMETRY değil) — metre bazlı mesafe hesaplamaları.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import (
    DateTime,
    Index,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class DepremRisk(Base):
    """
    Deprem risk modeli — konum bazlı sismik risk verileri.

    PostGIS GEOGRAPHY POINT ile konum, GiST index ile hızlı mekansal sorgulama.
    AFAD, TBDY ve zemin etüdü verilerini birleştirir.
    """

    __tablename__ = "deprem_risks"

    # ─── Primary Key ───────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )

    # ─── Konum ─────────────────────────────────────────────────────────
    location = mapped_column(
        Geography("POINT", srid=4326, spatial_index=True),
        nullable=False,
        comment="PostGIS GEOGRAPHY POINT — metre bazlı ST_Distance",
    )
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str] = mapped_column(String(100), nullable=False)
    neighborhood: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # ─── Risk Verileri ────────────────────────────────────────────────
    risk_score: Mapped[Decimal] = mapped_column(
        Numeric(5, 2),
        nullable=False,
        comment="Genel deprem risk skoru 0-100",
    )
    pga_value: Mapped[Decimal | None] = mapped_column(
        Numeric(6, 4),
        comment="Peak Ground Acceleration (g cinsinden)",
    )
    soil_class: Mapped[str | None] = mapped_column(
        String(10),
        comment="TBDY zemin sınıfı: ZA, ZB, ZC, ZD, ZE",
    )
    building_code_era: Mapped[str | None] = mapped_column(
        String(50),
        comment="Yapı yönetmeliği dönemi: pre_1999, 1999_2018, post_2018",
    )
    fault_distance_km: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2),
        comment="En yakın fay hattına mesafe (km)",
    )

    # ─── PROVENANCE ALANLARI (ADR-0006) ──────────────────────────────
    data_sources: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
        server_default=text("'[]'::jsonb"),
        comment='[{"source": "AFAD", "version": "2024", "fetched_at": "...", "record_count": 1}]',
    )
    provenance_version: Mapped[str | None] = mapped_column(
        String(50),
        comment="Veri versiyonu (ör: TBDY-2018-rev2)",
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
            name="uq_deprem_city_district_neighborhood",
        ),
        # GiST index for spatial queries — geoalchemy2 spatial_index=True
        # creates this automatically, but we keep explicit reference for clarity.
        Index("ix_deprem_city_district", "city", "district"),
        Index("ix_deprem_risk_score", "risk_score"),
    )

    def __repr__(self) -> str:
        parts = [self.city, self.district]
        if self.neighborhood:
            parts.append(self.neighborhood)
        return f"<DepremRisk {'/'.join(parts)} score={self.risk_score}>"
