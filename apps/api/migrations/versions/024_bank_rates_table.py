"""bank_rates_table

Revision ID: 024_bank_rates_table
Revises: 023_customer_demographics
Create Date: 2026-03-01

Banka konut kredisi faiz oranlari tablosu.

- bank_rates tablosu CREATE (tenant-bagimsiz, RLS YOK)
- 6 banka seed data INSERT (mevcut DEFAULT_BANK_RATES degerleri)
- idx_bank_rates_active_updated indeksi

NOT: RLS policy YOKTUR — bank_rates global referans verisidir,
tum ofisler ayni oranlari gorur. GRANT app_user eklenir cunku
RLS'li session'dan (SET LOCAL app.current_user_role) da erisilebilmeli.

Referans: TASK-193
"""

from collections.abc import Sequence
from datetime import datetime, timezone

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic
revision: str = "024_bank_rates_table"
down_revision: str = "023_customer_demographics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Seed data — mevcut DEFAULT_BANK_RATES ile birebir
_SEED_RATES = [
    {
        "bank_name": "Ziraat Bankası",
        "annual_rate": 3.09,
        "min_term": 12,
        "max_term": 120,
        "min_amount": 100_000.00,
        "max_amount": 10_000_000.00,
        "is_active": True,
        "update_source": "seed",
        "updated_at": datetime(2025, 2, 1, tzinfo=timezone.utc),
    },
    {
        "bank_name": "Halkbank",
        "annual_rate": 3.19,
        "min_term": 12,
        "max_term": 120,
        "min_amount": 100_000.00,
        "max_amount": 10_000_000.00,
        "is_active": True,
        "update_source": "seed",
        "updated_at": datetime(2025, 2, 1, tzinfo=timezone.utc),
    },
    {
        "bank_name": "Vakıfbank",
        "annual_rate": 3.29,
        "min_term": 12,
        "max_term": 120,
        "min_amount": 100_000.00,
        "max_amount": 10_000_000.00,
        "is_active": True,
        "update_source": "seed",
        "updated_at": datetime(2025, 2, 1, tzinfo=timezone.utc),
    },
    {
        "bank_name": "İş Bankası",
        "annual_rate": 3.39,
        "min_term": 12,
        "max_term": 96,
        "min_amount": 150_000.00,
        "max_amount": 8_000_000.00,
        "is_active": True,
        "update_source": "seed",
        "updated_at": datetime(2025, 2, 1, tzinfo=timezone.utc),
    },
    {
        "bank_name": "Garanti BBVA",
        "annual_rate": 3.49,
        "min_term": 12,
        "max_term": 120,
        "min_amount": 100_000.00,
        "max_amount": 10_000_000.00,
        "is_active": True,
        "update_source": "seed",
        "updated_at": datetime(2025, 2, 1, tzinfo=timezone.utc),
    },
    {
        "bank_name": "Yapı Kredi",
        "annual_rate": 3.44,
        "min_term": 12,
        "max_term": 120,
        "min_amount": 100_000.00,
        "max_amount": 10_000_000.00,
        "is_active": True,
        "update_source": "seed",
        "updated_at": datetime(2025, 2, 1, tzinfo=timezone.utc),
    },
]


def upgrade() -> None:
    # 1) Tablo olustur
    bank_rates = op.create_table(
        "bank_rates",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("bank_name", sa.String(100), nullable=False),
        sa.Column("annual_rate", sa.Numeric(5, 2), nullable=False),
        sa.Column("min_term", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("max_term", sa.Integer(), nullable=False, server_default="120"),
        sa.Column(
            "min_amount", sa.Numeric(15, 2), nullable=False, server_default="100000"
        ),
        sa.Column(
            "max_amount", sa.Numeric(15, 2), nullable=False, server_default="10000000"
        ),
        sa.Column(
            "is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")
        ),
        sa.Column(
            "update_source",
            sa.String(50),
            nullable=False,
            server_default="manual",
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bank_name", name="uq_bank_rates_bank_name"),
    )

    # 2) Performans indeksi
    op.create_index(
        "idx_bank_rates_active_updated",
        "bank_rates",
        ["is_active", sa.text("updated_at DESC")],
    )

    # 3) GRANT app_user (RLS session'larindan erisim icin)
    op.execute("GRANT SELECT ON bank_rates TO app_user")

    # 4) Seed data
    op.bulk_insert(bank_rates, _SEED_RATES)


def downgrade() -> None:
    op.drop_index("idx_bank_rates_active_updated", table_name="bank_rates")
    op.execute("REVOKE ALL ON bank_rates FROM app_user")
    op.drop_table("bank_rates")
