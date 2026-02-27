"""area_demographics

Revision ID: 015_area_demographics
Revises: 014_usage_quotas
Create Date: 2026-02-21

area_analyses tablosuna TÜİK demografik veri kolonları ekler:
- median_age, yaş grubu yüzdeleri (0-14, 15-24, 25-44, 45-64, 65+)
- population_density, household_count, avg_household_size

Tüm kolonlar nullable — mevcut kayıtlara etkisi yok.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "015_area_demographics"
down_revision: str | None = "014_usage_quotas"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ================================================================
    # area_analyses — 9 yeni demografik kolon (nullable)
    # ================================================================
    op.add_column(
        "area_analyses",
        sa.Column(
            "median_age", sa.Numeric(4, 1),
            nullable=True, comment="Medyan yaş",
        ),
    )
    op.add_column(
        "area_analyses",
        sa.Column(
            "age_0_14_pct", sa.Numeric(5, 2),
            nullable=True, comment="0-14 yaş yüzdesi",
        ),
    )
    op.add_column(
        "area_analyses",
        sa.Column(
            "age_15_24_pct", sa.Numeric(5, 2),
            nullable=True, comment="15-24 yaş yüzdesi",
        ),
    )
    op.add_column(
        "area_analyses",
        sa.Column(
            "age_25_44_pct", sa.Numeric(5, 2),
            nullable=True, comment="25-44 yaş yüzdesi",
        ),
    )
    op.add_column(
        "area_analyses",
        sa.Column(
            "age_45_64_pct", sa.Numeric(5, 2),
            nullable=True, comment="45-64 yaş yüzdesi",
        ),
    )
    op.add_column(
        "area_analyses",
        sa.Column(
            "age_65_plus_pct", sa.Numeric(5, 2),
            nullable=True, comment="65+ yaş yüzdesi",
        ),
    )
    op.add_column(
        "area_analyses",
        sa.Column(
            "population_density", sa.Integer(),
            nullable=True, comment="Nüfus yoğunluğu (kişi/km²)",
        ),
    )
    op.add_column(
        "area_analyses",
        sa.Column(
            "household_count", sa.Integer(),
            nullable=True, comment="Hane sayısı",
        ),
    )
    op.add_column(
        "area_analyses",
        sa.Column(
            "avg_household_size", sa.Numeric(3, 1),
            nullable=True, comment="Ortalama hane büyüklüğü",
        ),
    )


def downgrade() -> None:
    # Ters sıra ile kaldır
    op.drop_column("area_analyses", "avg_household_size")
    op.drop_column("area_analyses", "household_count")
    op.drop_column("area_analyses", "population_density")
    op.drop_column("area_analyses", "age_65_plus_pct")
    op.drop_column("area_analyses", "age_45_64_pct")
    op.drop_column("area_analyses", "age_25_44_pct")
    op.drop_column("area_analyses", "age_15_24_pct")
    op.drop_column("area_analyses", "age_0_14_pct")
    op.drop_column("area_analyses", "median_age")
