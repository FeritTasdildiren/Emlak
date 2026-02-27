"""outbox_inbox_events

Revision ID: 005_outbox_inbox_events
Revises: 004_payment_table
Create Date: 2026-02-20

Outbox + Inbox event tabloları:

1. outbox_events: Transactional Outbox pattern — domain event'leri
   aynı transaction'da yazılır, worker tarafından asenkron işlenir.
2. inbox_events: Inbox pattern — gelen event'lerin idempotent
   işlenmesi (event_id UNIQUE).
3. RLS: ENABLE + FORCE, tenant_isolation policy.
4. app_user GRANT.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "005_outbox_inbox_events"
down_revision: Union[str, None] = "004_payment_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # 1. outbox_events tablosu
    # ================================================================
    op.create_table(
        "outbox_events",
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
            "event_type", sa.String(100),
            nullable=False,
            comment="Event tipi (ör: property.created, payment.completed)",
        ),
        sa.Column(
            "aggregate_type", sa.String(100),
            nullable=False,
            comment="Aggregate tipi (ör: Property, Payment)",
        ),
        sa.Column(
            "aggregate_id", sa.UUID(),
            nullable=False,
            comment="Aggregate entity ID",
        ),
        sa.Column(
            "payload", postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
            comment="Event payload (JSON)",
        ),
        sa.Column(
            "status", sa.String(20),
            server_default=sa.text("'pending'"),
            nullable=False,
            comment="Event durumu: pending, processing, sent, failed, dead_letter",
        ),
        sa.Column(
            "locked_at", sa.DateTime(timezone=True),
            nullable=True,
            comment="Worker tarafından kilitlenme zamanı",
        ),
        sa.Column(
            "locked_by", sa.String(100),
            nullable=True,
            comment="Kilitleyen worker ID",
        ),
        sa.Column(
            "processed_at", sa.DateTime(timezone=True),
            nullable=True,
            comment="İşlenme zamanı",
        ),
        sa.Column(
            "retry_count", sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Tekrar deneme sayısı",
        ),
        sa.Column(
            "max_retries", sa.Integer(),
            server_default=sa.text("5"),
            nullable=False,
            comment="Maksimum tekrar deneme sayısı",
        ),
        sa.Column(
            "next_retry_at", sa.DateTime(timezone=True),
            nullable=True,
            comment="Sonraki tekrar deneme zamanı",
        ),
        sa.Column(
            "error_message", sa.String(),
            nullable=True,
            comment="Son hata mesajı",
        ),
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
    # 2. outbox_events indeksleri
    # ================================================================
    op.create_index(
        "ix_outbox_status_next_retry",
        "outbox_events",
        ["status", "next_retry_at"],
    )
    op.create_index(
        "ix_outbox_aggregate",
        "outbox_events",
        ["aggregate_type", "aggregate_id"],
    )

    # ================================================================
    # 3. inbox_events tablosu
    # ================================================================
    op.create_table(
        "inbox_events",
        sa.Column(
            "id", sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "office_id", sa.UUID(),
            nullable=True,
            comment="Bağlı ofis (tenant) ID — platform-level event'ler için NULL",
        ),
        sa.Column(
            "event_id", sa.String(200),
            nullable=False,
            comment="Kaynak sistemdeki benzersiz event ID (idempotency key)",
        ),
        sa.Column(
            "source", sa.String(100),
            nullable=False,
            comment="Event kaynağı (ör: payment-gateway, notification-service)",
        ),
        sa.Column(
            "event_type", sa.String(100),
            nullable=False,
            comment="Event tipi (ör: payment.webhook, sms.delivery_report)",
        ),
        sa.Column(
            "payload", postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
            comment="Event payload (JSON)",
        ),
        sa.Column(
            "status", sa.String(20),
            server_default=sa.text("'received'"),
            nullable=False,
            comment="Event durumu: received, processing, processed, failed",
        ),
        sa.Column(
            "processed_at", sa.DateTime(timezone=True),
            nullable=True,
            comment="İşlenme zamanı",
        ),
        sa.Column(
            "error_message", sa.String(),
            nullable=True,
            comment="Hata mesajı",
        ),
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
    # 4. inbox_events indeksleri
    # ================================================================
    op.create_index(
        "ix_inbox_events_event_id",
        "inbox_events",
        ["event_id"],
        unique=True,
    )

    # ================================================================
    # 5. RLS: ENABLE + FORCE + tenant_isolation policy
    # ================================================================
    for table in ("outbox_events", "inbox_events"):
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
        op.execute(sa.text(
            f"CREATE POLICY tenant_isolation_{table} ON {table} "
            f"USING (office_id = current_setting('app.current_office_id', true)::uuid)"
        ))

    # ================================================================
    # 6. app_user GRANT
    # ================================================================
    for table in ("outbox_events", "inbox_events"):
        op.execute(sa.text(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO app_user"
        ))


def downgrade() -> None:
    # --- app_user GRANT geri al ---
    for table in ("outbox_events", "inbox_events"):
        op.execute(sa.text(f"REVOKE ALL ON {table} FROM app_user"))

    # --- RLS policy ve kuralları kaldır ---
    for table in ("outbox_events", "inbox_events"):
        op.execute(sa.text(
            f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}"
        ))
        op.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))

    # --- inbox_events indeksleri ve tablosu kaldır ---
    op.drop_index("ix_inbox_events_event_id", table_name="inbox_events")
    op.drop_table("inbox_events")

    # --- outbox_events indeksleri ve tablosu kaldır ---
    op.drop_index("ix_outbox_aggregate", table_name="outbox_events")
    op.drop_index("ix_outbox_status_next_retry", table_name="outbox_events")
    op.drop_table("outbox_events")
