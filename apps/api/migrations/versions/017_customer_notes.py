"""customer_notes

Revision ID: 017_customer_notes
Revises: 016_customer_update_match_model
Create Date: 2026-02-22

customer_notes tablosu:
1. CREATE TABLE + indexler
2. RLS: ENABLE + FORCE + tenant_isolation policy
3. app_user GRANT: SELECT, INSERT, UPDATE, DELETE
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "017_customer_notes"
down_revision: str | None = "016_customer_update_match_model"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ================================================================
    # 1. customer_notes tablosu — CREATE TABLE
    # ================================================================
    op.create_table(
        "customer_notes",
        sa.Column(
            "id", sa.UUID(),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("now()"),
        ),
        sa.Column(
            "office_id", sa.UUID(),
            sa.ForeignKey("offices.id", ondelete="RESTRICT"),
            nullable=False,
            comment="Bağlı ofis (tenant) ID",
        ),
        sa.Column(
            "customer_id", sa.UUID(),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
            comment="İlişkili müşteri ID",
        ),
        sa.Column(
            "user_id", sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            comment="Notu oluşturan kullanıcı ID (silinirse NULL)",
        ),
        sa.Column(
            "content", sa.Text(),
            nullable=False,
            comment="Not içeriği",
        ),
        sa.Column(
            "note_type", sa.String(20),
            nullable=False, server_default=sa.text("'note'"),
            comment="Not tipi: note, call, meeting, email",
        ),
    )

    # ================================================================
    # 2. customer_notes — Indexler
    # ================================================================
    op.create_index(
        "ix_customer_notes_customer_id",
        "customer_notes",
        ["customer_id"],
    )
    op.create_index(
        "ix_customer_notes_office_id",
        "customer_notes",
        ["office_id"],
    )

    # ================================================================
    # 3. customer_notes — RLS: ENABLE + FORCE + POLICY
    # ================================================================
    op.execute(sa.text(
        "ALTER TABLE customer_notes ENABLE ROW LEVEL SECURITY"
    ))
    op.execute(sa.text(
        "ALTER TABLE customer_notes FORCE ROW LEVEL SECURITY"
    ))
    op.execute(sa.text(
        "CREATE POLICY tenant_isolation_customer_notes "
        "ON customer_notes "
        "USING (office_id = current_setting('app.current_office_id', true)::uuid)"
    ))

    # ================================================================
    # 4. customer_notes — app_user GRANT
    # ================================================================
    op.execute(sa.text(
        "GRANT SELECT, INSERT, UPDATE, DELETE "
        "ON customer_notes TO app_user"
    ))


def downgrade() -> None:
    # --- customer_notes: app_user GRANT geri al ---
    op.execute(sa.text(
        "REVOKE ALL ON customer_notes FROM app_user"
    ))

    # --- customer_notes: RLS geri al ---
    op.execute(sa.text(
        "DROP POLICY IF EXISTS tenant_isolation_customer_notes "
        "ON customer_notes"
    ))
    op.execute(sa.text(
        "ALTER TABLE customer_notes DISABLE ROW LEVEL SECURITY"
    ))

    # --- customer_notes: Indexler geri al ---
    op.drop_index("ix_customer_notes_office_id", table_name="customer_notes")
    op.drop_index("ix_customer_notes_customer_id", table_name="customer_notes")

    # --- customer_notes: Tablo sil ---
    op.drop_table("customer_notes")
