"""usage_quota_expand

Revision ID: 018_usage_quota_expand
Revises: 017_customer_notes
Create Date: 2026-02-22

UsageQuota tablosuna yeni sayaç kolonları eklenir:
1. listings_used  — ilan kullanım sayacı
2. staging_used   — sahneleme kullanım sayacı
3. photos_used    — fotoğraf kullanım sayacı
4. credit_balance — ekstra kredi bakiyesi
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "018_usage_quota_expand"
down_revision: str | None = "017_customer_notes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ================================================================
    # 1. usage_quotas tablosuna yeni sayaç kolonları ekle
    # ================================================================
    op.add_column(
        "usage_quotas",
        sa.Column(
            "listings_used",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Bu dönemde oluşturulan ilan sayısı",
        ),
    )
    op.add_column(
        "usage_quotas",
        sa.Column(
            "staging_used",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Bu dönemde yapılan sahneleme sayısı",
        ),
    )
    op.add_column(
        "usage_quotas",
        sa.Column(
            "photos_used",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Bu dönemde yüklenen fotoğraf sayısı",
        ),
    )
    op.add_column(
        "usage_quotas",
        sa.Column(
            "credit_balance",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Ekstra kredi bakiyesi (kota aşımında kullanılır)",
        ),
    )


def downgrade() -> None:
    # --- Yeni kolonları kaldır (ters sırada) ---
    op.drop_column("usage_quotas", "credit_balance")
    op.drop_column("usage_quotas", "photos_used")
    op.drop_column("usage_quotas", "staging_used")
    op.drop_column("usage_quotas", "listings_used")
