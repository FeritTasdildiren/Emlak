"""
Emlak Teknoloji Platformu - ScrapedListing Model

Web'den toplanan emlak ilan verileri. Platform-level tablo (tenant yok).
Yuksek hacim tablosu — BIGSERIAL PK (UUID degil).
Immutable kayittir — scrape edildikten sonra guncellenmez.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geography
from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class ScrapedListing(Base):
    """
    Web'den toplanan emlak ilani.

    sahibinden, hepsiemlak, emlakjet gibi kaynaklardan
    scrape edilen ilan verileri. Degerleme modeli icin
    emsal veri kaynagi olarak kullanilir.
    """

    __tablename__ = "scraped_listings"
    __table_args__ = (
        UniqueConstraint(
            "source", "external_id",
            name="uq_scraped_source_external",
        ),
        Index("ix_scraped_city_district", "city", "district"),
        Index("ix_scraped_source", "source"),
        Index("ix_scraped_price", "price"),
        Index("ix_scraped_location", "location", postgresql_using="gist"),
        Index("ix_scraped_at", "scraped_at"),
    )

    # ---------- Primary Key (BIGSERIAL) ----------
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True,
    )

    # ---------- Kaynak bilgisi ----------
    source: Mapped[str] = mapped_column(
        String(50), nullable=False,
        comment="Kaynak site: sahibinden, hepsiemlak, emlakjet",
    )
    external_id: Mapped[str] = mapped_column(
        String(100), nullable=False,
        comment="Kaynak sitedeki ilan ID",
    )
    url: Mapped[str | None] = mapped_column(
        String(500), nullable=True,
        comment="Ilan URL'i",
    )

    # ---------- Ilan bilgileri ----------
    title: Mapped[str] = mapped_column(
        String(500), nullable=False,
        comment="Ilan basligi",
    )
    price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2), nullable=True,
        comment="Fiyat",
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False,
        default="TRY",
        server_default=text("'TRY'"),
        comment="Para birimi (ISO 4217)",
    )
    listing_type: Mapped[str | None] = mapped_column(
        String(10), nullable=True,
        comment="Ilan tipi: sale, rent",
    )
    property_type: Mapped[str | None] = mapped_column(
        String(30), nullable=True,
        comment="Emlak tipi: apartment, villa, land",
    )

    # ---------- Ozellikler ----------
    rooms: Mapped[str | None] = mapped_column(
        String(20), nullable=True,
        comment="Oda sayisi (orn: 2+1, 3+1)",
    )
    area_sqm: Mapped[Decimal | None] = mapped_column(
        Numeric(8, 2), nullable=True,
        comment="Alan (m2)",
    )
    floor_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Bulundugu kat",
    )
    building_age: Mapped[int | None] = mapped_column(
        Integer, nullable=True,
        comment="Bina yasi",
    )

    # ---------- Konum ----------
    location = mapped_column(
        Geography("POINT", srid=4326, spatial_index=False),
        nullable=True,
        comment="Konum koordinatlari (GEOGRAPHY POINT)",
    )
    city: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="Il",
    )
    district: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="Ilce",
    )
    neighborhood: Mapped[str | None] = mapped_column(
        String(100), nullable=True,
        comment="Mahalle",
    )

    # ---------- Ham veri ----------
    raw_data: Mapped[dict] = mapped_column(
        JSONB, nullable=False,
        server_default=text("'{}'::jsonb"),
        comment="Kaynak siteden alinan ham veri JSON",
    )

    # ---------- Zaman ----------
    scraped_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        comment="Scrape edilme zamani",
    )
    listing_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Ilanin yayinlanma tarihi",
    )
