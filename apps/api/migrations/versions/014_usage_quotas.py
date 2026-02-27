"""usage_quotas

Revision ID: 014_usage_quotas
Revises: 013_turkish_search_config
Create Date: 2026-02-21

Aylık değerleme kota takibi:
1. usage_quotas tablosu (tenant-scoped, office_id FK)
2. Unique constraint: (office_id, period_start) — bir ofis bir ayda tek kayıt
3. RLS: ENABLE + FORCE + tenant_isolation policy
4. app_user GRANT: SELECT, INSERT, UPDATE
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "014_usage_quotas"
down_revision: Union[str, None] = "013_turkish_search_config"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # 1. usage_quotas tablosu (tenant-scoped)
    # ================================================================
    op.create_table(
        "usage_quotas",
        sa.Column(
            "id", sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "office_id", sa.UUID(),
            nullable=False,
            comment="Bağlı ofis (tenant) ID",
        ),
        sa.Column(
            "period_start", sa.Date(),
            nullable=False,
            comment="Kota dönem başlangıcı (ayın ilk günü)",
        ),
        sa.Column(
            "period_end", sa.Date(),
            nullable=False,
            comment="Kota dönem bitişi (ayın son günü)",
        ),
        sa.Column(
            "valuations_used", sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Bu dönemde yapılan değerleme sayısı",
        ),
        sa.Column(
            "valuations_limit", sa.Integer(),
            nullable=False,
            comment="Plan bazlı aylık değerleme limiti",
        ),
        # ---------- Timestamps ----------
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["office_id"], ["offices.id"], ondelete="RESTRICT",
        ),
        sa.UniqueConstraint(
            "office_id", "period_start",
            name="uq_usage_quotas_office_period",
        ),
    )

    # ================================================================
    # 2. İndeksler
    # ================================================================
    op.create_index(
        "ix_usage_quotas_office_id",
        "usage_quotas",
        ["office_id"],
    )

    # ================================================================
    # 3. RLS: ENABLE + FORCE + tenant_isolation policy
    # ================================================================
    op.execute(sa.text(
        "ALTER TABLE usage_quotas ENABLE ROW LEVEL SECURITY"
    ))
    op.execute(sa.text(
        "ALTER TABLE usage_quotas FORCE ROW LEVEL SECURITY"
    ))
    op.execute(sa.text(
        "CREATE POLICY usage_quotas_tenant_isolation ON usage_quotas "
        "USING (office_id = current_setting('app.current_office_id', true)::uuid)"
    ))

    # ================================================================
    # 4. app_user GRANT
    # ================================================================
    op.execute(sa.text(
        "GRANT SELECT, INSERT, UPDATE ON usage_quotas TO app_user"
    ))


def downgrade() -> None:
    # --- app_user GRANT geri al ---
    op.execute(sa.text("REVOKE ALL ON usage_quotas FROM app_user"))

    # --- RLS policy ve kuralları kaldır ---
    op.execute(sa.text(
        "DROP POLICY IF EXISTS usage_quotas_tenant_isolation ON usage_quotas"
    ))
    op.execute(sa.text(
        "ALTER TABLE usage_quotas DISABLE ROW LEVEL SECURITY"
    ))

    # --- İndeksleri kaldır ---
    op.drop_index("ix_usage_quotas_office_id", table_name="usage_quotas")

    # --- Tabloyu kaldır ---
    op.drop_table("usage_quotas")
