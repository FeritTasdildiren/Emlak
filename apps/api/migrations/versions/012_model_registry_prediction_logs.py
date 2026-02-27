"""model_registry_prediction_logs

Revision ID: 012_model_registry_prediction_logs
Revises: 011_property_fts_trigger
Create Date: 2026-02-21

ML model tablolari:
1. model_registry tablosu (platform geneli, RLS yok)
2. prediction_logs tablosu (tenant-scoped, RLS var)
3. RLS: ENABLE + FORCE + tenant_isolation policy (prediction_logs)
4. app_user GRANT: model_registry (SELECT, INSERT, UPDATE), prediction_logs (SELECT, INSERT)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "012_model_registry_prediction_logs"
down_revision: Union[str, None] = "011_property_fts_trigger"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # 1. model_registry tablosu (platform geneli — RLS yok)
    # ================================================================
    op.create_table(
        "model_registry",
        sa.Column(
            "id", sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "model_name", sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "version", sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "artifact_url", sa.String(500),
            nullable=False,
        ),
        sa.Column(
            "metrics", postgresql.JSON(),
            nullable=True,
        ),
        sa.Column(
            "training_data_size", sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "feature_count", sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "status", sa.String(20),
            server_default=sa.text("'active'"),
            nullable=False,
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
        sa.UniqueConstraint("model_name", "version", name="uq_model_registry_name_version"),
    )

    # model_name indeksi
    op.create_index(
        "ix_model_registry_model_name",
        "model_registry",
        ["model_name"],
    )

    # ================================================================
    # 2. prediction_logs tablosu (tenant-scoped)
    # ================================================================
    op.create_table(
        "prediction_logs",
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
            "model_name", sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "model_version", sa.String(20),
            nullable=False,
        ),
        sa.Column(
            "input_data", postgresql.JSON(),
            nullable=False,
        ),
        sa.Column(
            "output_data", postgresql.JSON(),
            nullable=False,
        ),
        sa.Column(
            "confidence", sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "latency_ms", sa.Integer(),
            nullable=True,
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
            ["office_id"], ["offices.id"], ondelete="RESTRICT"
        ),
    )

    # ================================================================
    # 3. prediction_logs indeksleri
    # ================================================================
    # Composite index: model + versiyon + zaman bazli sorgular
    op.create_index(
        "ix_prediction_logs_model_time",
        "prediction_logs",
        ["model_name", "model_version", "created_at"],
    )
    # office_id: Tenant bazli sorgular icin
    op.create_index(
        "ix_prediction_logs_office_id",
        "prediction_logs",
        ["office_id"],
    )

    # ================================================================
    # 4. RLS: ENABLE + FORCE + tenant_isolation policy (prediction_logs)
    # ================================================================
    op.execute(sa.text("ALTER TABLE prediction_logs ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE prediction_logs FORCE ROW LEVEL SECURITY"))
    op.execute(sa.text(
        "CREATE POLICY prediction_logs_tenant_isolation ON prediction_logs "
        "USING (office_id = current_setting('app.current_office_id', true)::uuid)"
    ))

    # ================================================================
    # 5. app_user GRANT
    # ================================================================
    op.execute(sa.text(
        "GRANT SELECT, INSERT, UPDATE ON model_registry TO app_user"
    ))
    op.execute(sa.text(
        "GRANT SELECT, INSERT ON prediction_logs TO app_user"
    ))


def downgrade() -> None:
    # --- app_user GRANT geri al ---
    op.execute(sa.text("REVOKE ALL ON prediction_logs FROM app_user"))
    op.execute(sa.text("REVOKE ALL ON model_registry FROM app_user"))

    # --- RLS policy ve kurallari kaldir (prediction_logs) ---
    op.execute(sa.text(
        "DROP POLICY IF EXISTS prediction_logs_tenant_isolation ON prediction_logs"
    ))
    op.execute(sa.text("ALTER TABLE prediction_logs DISABLE ROW LEVEL SECURITY"))

    # --- Indeksleri kaldir ---
    op.drop_index("ix_prediction_logs_office_id", table_name="prediction_logs")
    op.drop_index("ix_prediction_logs_model_time", table_name="prediction_logs")
    op.drop_index("ix_model_registry_model_name", table_name="model_registry")

    # --- Tablolari kaldir ---
    op.drop_table("prediction_logs")
    op.drop_table("model_registry")
