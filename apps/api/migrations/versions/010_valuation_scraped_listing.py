"""valuation_scraped_listing

Revision ID: 010_valuation_scraped_listing
Revises: 009_area_deprem_price_models
Create Date: 2026-02-20

PropertyValuation ve ScrapedListing tablolarini olusturur:
1. property_valuations — Emlak degerleme sonuclari (multi-tenant, UUID PK)
2. scraped_listings    — Web'den toplanan ilan verileri (platform-level, BIGSERIAL PK)

PostGIS GEOGRAPHY tipi kullanilir (GEOMETRY degil).
"""

from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "010_valuation_scraped_listing"
down_revision: Union[str, None] = "009_area_deprem_price_models"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # PostGIS extension — zaten 001'de oluşturuluyor, defensive check
    # ================================================================
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS postgis"))

    # ================================================================
    # 1. PROPERTY_VALUATIONS — Emlak degerleme sonuclari
    # ================================================================
    op.create_table(
        "property_valuations",
        # PK
        sa.Column(
            "id", sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # Multi-tenant
        sa.Column(
            "office_id", sa.UUID(),
            sa.ForeignKey("offices.id", ondelete="RESTRICT"),
            nullable=False,
            comment="Bagli ofis (tenant) ID",
        ),
        sa.Column(
            "user_id", sa.UUID(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
            comment="Degerleme yapan kullanici ID",
        ),
        # Opsiyonel bagli mulk
        sa.Column(
            "property_id", sa.UUID(),
            sa.ForeignKey("properties.id", ondelete="SET NULL"),
            nullable=True,
            comment="Bagli mulk ID (opsiyonel)",
        ),
        # Degerleme adresi ve konum
        sa.Column("address", sa.Text(), nullable=False, comment="Acik adres"),
        sa.Column(
            "location",
            geoalchemy2.types.Geography("POINT", srid=4326, spatial_index=True),
            nullable=False,
            comment="Konum koordinatlari (GEOGRAPHY POINT)",
        ),
        sa.Column("city", sa.String(100), nullable=False, comment="Il"),
        sa.Column("district", sa.String(100), nullable=False, comment="Ilce"),
        sa.Column("neighborhood", sa.String(100), nullable=True, comment="Mahalle"),
        # Girdi parametreleri
        sa.Column(
            "input_params", postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            comment="Degerleme girdi parametreleri JSON",
        ),
        # Tahmin sonuclari
        sa.Column(
            "estimated_price_min", sa.Numeric(15, 2), nullable=False,
            comment="Tahmini minimum fiyat (TL)",
        ),
        sa.Column(
            "estimated_price_max", sa.Numeric(15, 2), nullable=False,
            comment="Tahmini maksimum fiyat (TL)",
        ),
        sa.Column(
            "estimated_price_avg", sa.Numeric(15, 2), nullable=False,
            comment="Tahmini ortalama fiyat (TL)",
        ),
        sa.Column(
            "confidence_score", sa.Numeric(5, 4), nullable=False,
            comment="Guven skoru 0.0000 - 1.0000",
        ),
        # Model bilgisi
        sa.Column(
            "model_version", sa.String(50), nullable=False,
            comment="ML model versiyon bilgisi",
        ),
        # Emsal veriler
        sa.Column(
            "comparables", postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"), nullable=False,
            comment="Emsal verileri JSON listesi",
        ),
        # Fiyat metrikleri
        sa.Column(
            "price_per_sqm", sa.Numeric(10, 2), nullable=True,
            comment="Metrekare birim fiyat (TL/m2)",
        ),
        sa.Column(
            "area_avg_price_per_sqm", sa.Numeric(10, 2), nullable=True,
            comment="Bolge ortalama metrekare birim fiyat (TL/m2)",
        ),
        # Rapor
        sa.Column(
            "report_url", sa.String(500), nullable=True,
            comment="Degerleme raporu URL",
        ),
        # Zaman
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
    )

    # property_valuations indexes
    op.create_index("ix_valuations_office", "property_valuations", ["office_id"])
    op.create_index("ix_valuations_user", "property_valuations", ["user_id"])
    op.create_index("ix_valuations_property", "property_valuations", ["property_id"])
    op.create_index("ix_valuations_city_district", "property_valuations", ["city", "district"])
    op.create_index("ix_valuations_created", "property_valuations", ["created_at"])

    # ================================================================
    # 2. SCRAPED_LISTINGS — Web'den toplanan ilan verileri
    # ================================================================
    op.create_table(
        "scraped_listings",
        # PK (BIGSERIAL — yuksek hacim tablosu, UUID overhead'inden kacinilir)
        sa.Column(
            "id", sa.BigInteger(),
            autoincrement=True, nullable=False,
        ),
        # Kaynak bilgisi
        sa.Column(
            "source", sa.String(50), nullable=False,
            comment="Kaynak site: sahibinden, hepsiemlak, emlakjet",
        ),
        sa.Column(
            "external_id", sa.String(100), nullable=False,
            comment="Kaynak sitedeki ilan ID",
        ),
        sa.Column(
            "url", sa.String(500), nullable=True,
            comment="Ilan URL'i",
        ),
        # Ilan bilgileri
        sa.Column(
            "title", sa.String(500), nullable=False,
            comment="Ilan basligi",
        ),
        sa.Column(
            "price", sa.Numeric(15, 2), nullable=True,
            comment="Fiyat",
        ),
        sa.Column(
            "currency", sa.String(3), nullable=False,
            server_default=sa.text("'TRY'"),
            comment="Para birimi (ISO 4217)",
        ),
        sa.Column(
            "listing_type", sa.String(10), nullable=True,
            comment="Ilan tipi: sale, rent",
        ),
        sa.Column(
            "property_type", sa.String(30), nullable=True,
            comment="Emlak tipi: apartment, villa, land",
        ),
        # Ozellikler
        sa.Column(
            "rooms", sa.String(20), nullable=True,
            comment="Oda sayisi (orn: 2+1, 3+1)",
        ),
        sa.Column(
            "area_sqm", sa.Numeric(8, 2), nullable=True,
            comment="Alan (m2)",
        ),
        sa.Column(
            "floor_number", sa.Integer(), nullable=True,
            comment="Bulundugu kat",
        ),
        sa.Column(
            "building_age", sa.Integer(), nullable=True,
            comment="Bina yasi",
        ),
        # Konum
        sa.Column(
            "location",
            geoalchemy2.types.Geography("POINT", srid=4326, spatial_index=False),
            nullable=True,
            comment="Konum koordinatlari (GEOGRAPHY POINT)",
        ),
        sa.Column(
            "city", sa.String(100), nullable=True,
            comment="Il",
        ),
        sa.Column(
            "district", sa.String(100), nullable=True,
            comment="Ilce",
        ),
        sa.Column(
            "neighborhood", sa.String(100), nullable=True,
            comment="Mahalle",
        ),
        # Ham veri
        sa.Column(
            "raw_data", postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"), nullable=False,
            comment="Kaynak siteden alinan ham veri JSON",
        ),
        # Zaman
        sa.Column(
            "scraped_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
            comment="Scrape edilme zamani",
        ),
        sa.Column(
            "listing_date", sa.DateTime(timezone=True), nullable=True,
            comment="Ilanin yayinlanma tarihi",
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "source", "external_id",
            name="uq_scraped_source_external",
        ),
    )

    # scraped_listings indexes
    op.create_index("ix_scraped_city_district", "scraped_listings", ["city", "district"])
    op.create_index("ix_scraped_source", "scraped_listings", ["source"])
    op.create_index("ix_scraped_price", "scraped_listings", ["price"])
    op.create_index(
        "ix_scraped_location", "scraped_listings", ["location"],
        postgresql_using="gist",
    )
    op.create_index("ix_scraped_at", "scraped_listings", ["scraped_at"])


def downgrade() -> None:
    # ================================================================
    # Ters sira ile temizlik
    # ================================================================

    # --- scraped_listings indexes ---
    op.drop_index("ix_scraped_at", table_name="scraped_listings")
    op.drop_index("ix_scraped_location", table_name="scraped_listings")
    op.drop_index("ix_scraped_price", table_name="scraped_listings")
    op.drop_index("ix_scraped_source", table_name="scraped_listings")
    op.drop_index("ix_scraped_city_district", table_name="scraped_listings")

    # --- property_valuations indexes ---
    op.drop_index("ix_valuations_created", table_name="property_valuations")
    op.drop_index("ix_valuations_city_district", table_name="property_valuations")
    op.drop_index("ix_valuations_property", table_name="property_valuations")
    op.drop_index("ix_valuations_user", table_name="property_valuations")
    op.drop_index("ix_valuations_office", table_name="property_valuations")

    # --- Tablolar (ters olusturma sirasinda) ---
    op.drop_table("scraped_listings")
    op.drop_table("property_valuations")
