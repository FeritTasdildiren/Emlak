"""area_deprem_price_models

Revision ID: 009_area_deprem_price_models
Revises: 008_user_telegram_chat_id
Create Date: 2026-02-20

Veri toplama pipeline temel tablolarını oluşturur:
1. area_analyses  — Bölge analiz verileri (fiyat, demografik, POI skorları)
2. deprem_risks   — Konum bazlı deprem risk verileri (PGA, zemin, fay mesafesi)
3. price_histories — Zaman serisi bölge fiyat geçmişi (BIGSERIAL PK)

Tüm tablolar platform-level'dır (office_id/tenant yok).
ADR-0006 kapsamında provenance alanları eklenir.
PostGIS GEOGRAPHY tipi kullanılır (GEOMETRY değil).
"""

from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "009_area_deprem_price_models"
down_revision: Union[str, None] = "008_user_telegram_chat_id"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # PostGIS extension — zaten 001'de oluşturuluyor, defensive check
    # ================================================================
    op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS postgis"))

    # ================================================================
    # 1. AREA_ANALYSES — Bölge analiz verileri
    # ================================================================
    op.create_table(
        "area_analyses",
        # PK
        sa.Column(
            "id", sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # Bölge Bilgileri
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=False),
        sa.Column("neighborhood", sa.String(100), nullable=True),
        sa.Column(
            "boundary",
            geoalchemy2.types.Geography("POLYGON", srid=4326, spatial_index=False),
            nullable=True,
        ),
        # Fiyat Verileri
        sa.Column("avg_price_sqm_sale", sa.Numeric(10, 2), nullable=True),
        sa.Column("avg_price_sqm_rent", sa.Numeric(10, 2), nullable=True),
        sa.Column(
            "price_trend_6m", sa.Numeric(5, 2), nullable=True,
            comment="Son 6 aylık fiyat değişim yüzdesi",
        ),
        # Piyasa Verileri
        sa.Column("supply_demand_ratio", sa.Numeric(5, 2), nullable=True),
        sa.Column("listing_count", sa.Integer(), nullable=True),
        # Demografik Veriler
        sa.Column("population", sa.Integer(), nullable=True),
        sa.Column(
            "demographics", postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"), nullable=False,
            comment="Yaş dağılımı, eğitim seviyesi, gelir düzeyi",
        ),
        # POI ve Skorlar
        sa.Column(
            "poi_data", postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"), nullable=False,
            comment="Okul, hastane, metro, market mesafe/sayı bilgileri",
        ),
        sa.Column(
            "transport_score", sa.Numeric(5, 2), nullable=True,
            comment="Ulaşım skoru 0-100",
        ),
        sa.Column(
            "amenity_score", sa.Numeric(5, 2), nullable=True,
            comment="Yaşam kolaylığı skoru 0-100",
        ),
        sa.Column(
            "investment_score", sa.Numeric(5, 2), nullable=True,
            comment="Yatırım potansiyeli skoru 0-100",
        ),
        sa.Column(
            "amortization_years", sa.Numeric(5, 1), nullable=True,
            comment="Amortisman süresi (yıl)",
        ),
        # Provenance (ADR-0006)
        sa.Column(
            "data_sources", postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"), nullable=False,
        ),
        sa.Column("provenance_version", sa.String(50), nullable=True),
        sa.Column(
            "refresh_status", sa.String(20),
            server_default=sa.text("'fresh'"), nullable=False,
            comment="fresh | stale | refreshing | failed",
        ),
        sa.Column("last_refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "refresh_error", sa.Text(), nullable=True,
            comment="Son refresh hatası mesajı",
        ),
        # Zaman Damgaları
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "city", "district", "neighborhood",
            name="uq_area_city_district_neighborhood",
        ),
    )

    # area_analyses indexes
    op.create_index("ix_area_city_district", "area_analyses", ["city", "district"])
    op.create_index("ix_area_refresh_status", "area_analyses", ["refresh_status"])

    # ================================================================
    # 2. DEPREM_RISKS — Deprem risk verileri
    # ================================================================
    op.create_table(
        "deprem_risks",
        # PK
        sa.Column(
            "id", sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # Konum
        sa.Column(
            "location",
            geoalchemy2.types.Geography("POINT", srid=4326, spatial_index=True),
            nullable=False,
            comment="PostGIS GEOGRAPHY POINT — metre bazlı ST_Distance",
        ),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=False),
        sa.Column("neighborhood", sa.String(100), nullable=True),
        # Risk Verileri
        sa.Column(
            "risk_score", sa.Numeric(5, 2), nullable=False,
            comment="Genel deprem risk skoru 0-100",
        ),
        sa.Column(
            "pga_value", sa.Numeric(6, 4), nullable=True,
            comment="Peak Ground Acceleration (g cinsinden)",
        ),
        sa.Column(
            "soil_class", sa.String(10), nullable=True,
            comment="TBDY zemin sınıfı: ZA, ZB, ZC, ZD, ZE",
        ),
        sa.Column(
            "building_code_era", sa.String(50), nullable=True,
            comment="Yapı yönetmeliği dönemi: pre_1999, 1999_2018, post_2018",
        ),
        sa.Column(
            "fault_distance_km", sa.Numeric(8, 2), nullable=True,
            comment="En yakın fay hattına mesafe (km)",
        ),
        # Provenance (ADR-0006)
        sa.Column(
            "data_sources", postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"), nullable=False,
        ),
        sa.Column("provenance_version", sa.String(50), nullable=True),
        sa.Column(
            "refresh_status", sa.String(20),
            server_default=sa.text("'fresh'"), nullable=False,
            comment="fresh | stale | refreshing | failed",
        ),
        sa.Column("last_refreshed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "refresh_error", sa.Text(), nullable=True,
            comment="Son refresh hatası mesajı",
        ),
        # Zaman Damgaları
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "city", "district", "neighborhood",
            name="uq_deprem_city_district_neighborhood",
        ),
    )

    # deprem_risks indexes (GiST spatial index on location auto-created by geoalchemy2)
    op.create_index("ix_deprem_city_district", "deprem_risks", ["city", "district"])
    op.create_index("ix_deprem_risk_score", "deprem_risks", ["risk_score"])

    # ================================================================
    # 3. PRICE_HISTORIES — Fiyat geçmişi (BIGSERIAL PK)
    # ================================================================
    op.create_table(
        "price_histories",
        # PK (BIGSERIAL — yüksek hacim tablosu, UUID overhead'inden kaçınılır)
        sa.Column(
            "id", sa.BigInteger(),
            autoincrement=True, nullable=False,
        ),
        # Bölge Bilgileri
        sa.Column(
            "area_type", sa.String(20), nullable=False,
            comment="Granülerlik: neighborhood, district, city",
        ),
        sa.Column(
            "area_name", sa.String(100), nullable=False,
            comment="Bölge adı (mahalle/ilçe/şehir ismi)",
        ),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("district", sa.String(100), nullable=True),
        sa.Column(
            "date", sa.Date(), nullable=False,
            comment="Veri dönemi (aylık: ayın ilk günü)",
        ),
        # Fiyat Verileri
        sa.Column(
            "avg_price_sqm", sa.Numeric(10, 2), nullable=True,
            comment="Ortalama metrekare birim fiyat (TL)",
        ),
        sa.Column(
            "median_price", sa.Numeric(15, 2), nullable=True,
            comment="Medyan satış/kira fiyatı (TL)",
        ),
        sa.Column(
            "listing_count", sa.Integer(), nullable=True,
            comment="Dönemdeki ilan sayısı",
        ),
        sa.Column(
            "transaction_count", sa.Integer(), nullable=True,
            comment="Dönemdeki işlem (satış/kiralama) sayısı",
        ),
        # Provenance (ADR-0006)
        sa.Column(
            "source", sa.String(50), nullable=False,
            comment="Veri kaynağı: TUIK, TCMB, scraping",
        ),
        sa.Column(
            "provenance_version", sa.String(50), nullable=True,
            comment="Kaynak veri versiyonu",
        ),
        # Zaman Damgası
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"), nullable=False,
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "area_type", "area_name", "city", "date", "source",
            name="uq_price_area_date_source",
        ),
    )

    # price_histories indexes
    op.create_index("ix_price_city_date", "price_histories", ["city", "date"])
    op.create_index("ix_price_area_type", "price_histories", ["area_type", "area_name"])

    # ================================================================
    # updated_at trigger — tüm yeni tablolar için
    # ================================================================
    op.execute(sa.text("""
        CREATE OR REPLACE FUNCTION trigger_set_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """))

    # area_analyses updated_at trigger
    op.execute(sa.text("""
        CREATE TRIGGER trg_area_analyses_updated_at
        BEFORE UPDATE ON area_analyses
        FOR EACH ROW
        EXECUTE FUNCTION trigger_set_updated_at();
    """))

    # deprem_risks updated_at trigger
    op.execute(sa.text("""
        CREATE TRIGGER trg_deprem_risks_updated_at
        BEFORE UPDATE ON deprem_risks
        FOR EACH ROW
        EXECUTE FUNCTION trigger_set_updated_at();
    """))

    # price_histories tablosunda updated_at yok, trigger gerekmez


def downgrade() -> None:
    # ================================================================
    # Ters sıra ile temizlik
    # ================================================================

    # --- Triggers ---
    op.execute(sa.text(
        "DROP TRIGGER IF EXISTS trg_deprem_risks_updated_at ON deprem_risks"
    ))
    op.execute(sa.text(
        "DROP TRIGGER IF EXISTS trg_area_analyses_updated_at ON area_analyses"
    ))
    # NOT: trigger_set_updated_at fonksiyonu başka tablolar da kullanabilir,
    # bu yüzden silmiyoruz (idempotent CREATE OR REPLACE ile oluşturuluyor).

    # --- Indexes (tablolarla birlikte düşer ama explicit olarak da silelim) ---
    op.drop_index("ix_price_area_type", table_name="price_histories")
    op.drop_index("ix_price_city_date", table_name="price_histories")

    op.drop_index("ix_deprem_risk_score", table_name="deprem_risks")
    op.drop_index("ix_deprem_city_district", table_name="deprem_risks")

    op.drop_index("ix_area_refresh_status", table_name="area_analyses")
    op.drop_index("ix_area_city_district", table_name="area_analyses")

    # --- Tablolar (ters oluşturma sırasıyla) ---
    op.drop_table("price_histories")
    op.drop_table("deprem_risks")
    op.drop_table("area_analyses")
