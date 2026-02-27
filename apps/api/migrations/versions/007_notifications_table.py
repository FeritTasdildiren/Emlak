"""notifications_table

Revision ID: 007_notifications_table
Revises: 006_payment_timeline
Create Date: 2026-02-20

Bildirimler (notifications) tablosunu olusturur.

Degisiklikler:
1. notifications tablosu olusturulur (tum kolonlar + indeksler)
2. Composite index: ix_notifications_user_id_is_read (user_id + is_read)
3. Index: ix_notifications_office_id (tenant bazli sorgular)
4. RLS: ENABLE + FORCE + tenant_isolation policy
5. app_user GRANT: SELECT, INSERT, UPDATE, DELETE
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "007_notifications_table"
down_revision: Union[str, None] = "006_payment_timeline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # 1. notifications tablosu — 001_initial_schema'da zaten olusturuluyor
    #    Bu migration sadece eksik indeks, RLS ve GRANT islemlerini yapar.
    # ================================================================
    conn = op.get_bind()
    table_exists = conn.execute(sa.text(
        "SELECT EXISTS (SELECT FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_name = 'notifications')"
    )).scalar()

    if not table_exists:
        op.create_table(
            "notifications",
            sa.Column(
                "id", sa.UUID(),
                server_default=sa.text("gen_random_uuid()"),
                nullable=False,
            ),
            sa.Column(
                "user_id", sa.UUID(),
                nullable=False,
                comment="Hedef kullanici ID",
            ),
            sa.Column(
                "office_id", sa.UUID(),
                nullable=False,
                comment="Bagli ofis (tenant) ID",
            ),
            sa.Column(
                "type", sa.String(50),
                nullable=False,
                comment="Bildirim tipi: new_match, new_message, subscription_update vb.",
            ),
            sa.Column(
                "title", sa.String(255),
                nullable=False,
                comment="Bildirim basligi",
            ),
            sa.Column(
                "body", sa.Text(),
                nullable=True,
                comment="Bildirim detay metni",
            ),
            sa.Column(
                "is_read", sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
                comment="Okundu mu",
            ),
            sa.Column(
                "data", postgresql.JSONB(),
                server_default=sa.text("'{}'::jsonb"),
                nullable=False,
                comment="Bildirime ait ek veriler (JSON)",
            ),
            # ---------- Soft Delete ----------
            sa.Column(
                "deleted_at", sa.DateTime(timezone=True),
                nullable=True,
                comment="Silinme zamani (null = silinmemis)",
            ),
            sa.Column(
                "is_deleted", sa.Boolean(),
                server_default=sa.text("false"),
                nullable=False,
                comment="Soft-delete flag",
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
                ["user_id"], ["users.id"], ondelete="CASCADE"
            ),
            sa.ForeignKeyConstraint(
                ["office_id"], ["offices.id"], ondelete="RESTRICT"
            ),
        )
    else:
        # Tablo 001_initial_schema'da olusturulmus — eksik kolonlari ekle
        col_exists = conn.execute(sa.text(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'notifications' AND column_name = 'is_deleted')"
        )).scalar()
        if not col_exists:
            op.add_column("notifications", sa.Column(
                "deleted_at", sa.DateTime(timezone=True), nullable=True,
                comment="Silinme zamani (null = silinmemis)",
            ))
            op.add_column("notifications", sa.Column(
                "is_deleted", sa.Boolean(),
                server_default=sa.text("false"), nullable=False,
                comment="Soft-delete flag",
            ))

    # ================================================================
    # 2. Indeksler (IF NOT EXISTS semantigi)
    # ================================================================
    idx_exists = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_notifications_user_id_is_read')"
    )).scalar()
    if not idx_exists:
        op.create_index(
            "ix_notifications_user_id_is_read",
            "notifications",
            ["user_id", "is_read"],
        )

    idx2_exists = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM pg_indexes WHERE indexname = 'ix_notifications_office_id')"
    )).scalar()
    if not idx2_exists:
        op.create_index(
            "ix_notifications_office_id",
            "notifications",
            ["office_id"],
        )

    # ================================================================
    # 3. RLS: ENABLE + FORCE + tenant_isolation policy
    # ================================================================
    op.execute(sa.text("ALTER TABLE notifications ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE notifications FORCE ROW LEVEL SECURITY"))

    policy_exists = conn.execute(sa.text(
        "SELECT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'tenant_isolation_notifications')"
    )).scalar()
    if not policy_exists:
        op.execute(sa.text(
            "CREATE POLICY tenant_isolation_notifications ON notifications "
            "USING (office_id = current_setting('app.current_office_id', true)::uuid)"
        ))

    # ================================================================
    # 4. app_user GRANT
    # ================================================================
    op.execute(sa.text(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON notifications TO app_user"
    ))


def downgrade() -> None:
    # --- app_user GRANT geri al ---
    op.execute(sa.text("REVOKE ALL ON notifications FROM app_user"))

    # --- RLS policy ve kurallari kaldir ---
    op.execute(sa.text(
        "DROP POLICY IF EXISTS tenant_isolation_notifications ON notifications"
    ))
    op.execute(sa.text("ALTER TABLE notifications DISABLE ROW LEVEL SECURITY"))

    # --- Indeksleri kaldir ---
    op.drop_index("ix_notifications_office_id", table_name="notifications")
    op.drop_index("ix_notifications_user_id_is_read", table_name="notifications")

    # --- notifications tablosunu kaldir ---
    op.drop_table("notifications")
