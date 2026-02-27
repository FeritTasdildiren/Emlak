"""transaction_audit_log

Revision ID: 021_transaction_audit_log
Revises: 020_performance_indexes
Create Date: 2026-02-27

KVKK Audit Bulgulari #2 ve #3:
- Transaction tablosu: Odeme islem takibi (charge, refund, void, adjustment)
- AuditLog tablosu: KVKK uyumlu denetim kayitlari

Her iki tablo icin:
1. Tablo olusturma + indeksler
2. ENABLE + FORCE ROW LEVEL SECURITY
3. Tenant isolation policy (current_setting pattern)
4. GRANT ALL TO app_user
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "021_transaction_audit_log"
down_revision: str | None = "020_performance_indexes"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ================================================================
    # 1. TRANSACTIONS TABLOSU
    # ================================================================
    op.create_table(
        "transactions",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="Primary key UUID",
        ),
        sa.Column(
            "office_id",
            sa.UUID(),
            nullable=False,
            comment="Bagli ofis (tenant) ID",
        ),
        sa.Column(
            "payment_id",
            sa.UUID(),
            nullable=False,
            comment="Bagli odeme ID",
        ),
        sa.Column(
            "type",
            sa.String(20),
            nullable=False,
            comment="Islem tipi: charge, refund, void, adjustment",
        ),
        sa.Column(
            "amount",
            sa.Numeric(10, 2),
            nullable=False,
            comment="Islem tutari",
        ),
        sa.Column(
            "status",
            sa.String(20),
            server_default=sa.text("'pending'"),
            nullable=False,
            comment="Islem durumu: pending, completed, failed",
        ),
        sa.Column(
            "external_transaction_id",
            sa.String(100),
            nullable=True,
            comment="Odeme saglayici islem ID (duplicate engeli)",
        ),
        sa.Column(
            "metadata",
            sa.dialects.postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
            comment="Ek bilgiler JSON (saglayici yanitlari vb.)",
        ),
        sa.Column(
            "error_message",
            sa.String(),
            nullable=True,
            comment="Basarisiz islem hata mesaji",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["office_id"], ["offices.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["payment_id"], ["payments.id"], ondelete="RESTRICT"
        ),
    )

    # --- Transactions indeksleri ---
    op.create_index("ix_transactions_office_id", "transactions", ["office_id"])
    op.create_index("ix_transactions_payment_id", "transactions", ["payment_id"])
    op.create_index(
        "ix_transactions_external_transaction_id",
        "transactions",
        ["external_transaction_id"],
        unique=True,
        postgresql_where=sa.text("external_transaction_id IS NOT NULL"),
    )
    op.create_index("ix_transactions_status", "transactions", ["status"])
    op.create_index("ix_transactions_type", "transactions", ["type"])
    op.create_index("ix_transactions_created_at", "transactions", ["created_at"])

    # --- Transactions RLS ---
    op.execute(sa.text("ALTER TABLE transactions ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE transactions FORCE ROW LEVEL SECURITY"))
    op.execute(sa.text(
        "CREATE POLICY transactions_tenant_isolation ON transactions "
        "USING (office_id = current_setting('app.current_office_id', true)::uuid)"
    ))

    # --- Transactions GRANT ---
    op.execute(sa.text("GRANT ALL ON transactions TO app_user"))

    # ================================================================
    # 2. AUDIT_LOGS TABLOSU
    # ================================================================
    op.create_table(
        "audit_logs",
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
            comment="Primary key UUID",
        ),
        sa.Column(
            "office_id",
            sa.UUID(),
            nullable=False,
            comment="Bagli ofis (tenant) ID",
        ),
        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
            comment="Eylemi gerceklestiren kullanici ID",
        ),
        sa.Column(
            "action",
            sa.String(20),
            nullable=False,
            comment="Eylem tipi: CREATE, READ, UPDATE, DELETE, LOGIN, LOGOUT, EXPORT",
        ),
        sa.Column(
            "entity_type",
            sa.String(100),
            nullable=False,
            comment="Etkilenen varlik tipi (model adi)",
        ),
        sa.Column(
            "entity_id",
            sa.String(36),
            nullable=True,
            comment="Etkilenen varlik UUID",
        ),
        sa.Column(
            "old_value",
            sa.dialects.postgresql.JSONB(),
            nullable=True,
            comment="Degisiklik oncesi degerler",
        ),
        sa.Column(
            "new_value",
            sa.dialects.postgresql.JSONB(),
            nullable=True,
            comment="Degisiklik sonrasi degerler",
        ),
        sa.Column(
            "ip_address",
            sa.String(45),
            nullable=True,
            comment="Istemci IP adresi (IPv4/IPv6)",
        ),
        sa.Column(
            "user_agent",
            sa.String(500),
            nullable=True,
            comment="Istemci user agent bilgisi",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(
            ["office_id"], ["offices.id"], ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], ondelete="RESTRICT"
        ),
    )

    # --- AuditLog indeksleri ---
    op.create_index("ix_audit_logs_office_id", "audit_logs", ["office_id"])
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"])
    op.create_index(
        "ix_audit_logs_entity_type_entity_id",
        "audit_logs",
        ["entity_type", "entity_id"],
    )
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])
    op.create_index(
        "ix_audit_logs_office_created",
        "audit_logs",
        ["office_id", "created_at"],
    )

    # --- AuditLog RLS ---
    op.execute(sa.text("ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE audit_logs FORCE ROW LEVEL SECURITY"))
    op.execute(sa.text(
        "CREATE POLICY audit_logs_tenant_isolation ON audit_logs "
        "USING (office_id = current_setting('app.current_office_id', true)::uuid)"
    ))

    # --- AuditLog GRANT ---
    op.execute(sa.text("GRANT ALL ON audit_logs TO app_user"))


def downgrade() -> None:
    # ================================================================
    # AuditLog: GRANT → RLS → Index → Table (ters sira)
    # ================================================================
    op.execute(sa.text("REVOKE ALL ON audit_logs FROM app_user"))
    op.execute(
        sa.text("DROP POLICY IF EXISTS audit_logs_tenant_isolation ON audit_logs")
    )
    op.execute(sa.text("ALTER TABLE audit_logs DISABLE ROW LEVEL SECURITY"))

    op.drop_index("ix_audit_logs_office_created", table_name="audit_logs")
    op.drop_index("ix_audit_logs_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_action", table_name="audit_logs")
    op.drop_index(
        "ix_audit_logs_entity_type_entity_id", table_name="audit_logs"
    )
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_office_id", table_name="audit_logs")

    op.drop_table("audit_logs")

    # ================================================================
    # Transactions: GRANT → RLS → Index → Table (ters sira)
    # ================================================================
    op.execute(sa.text("REVOKE ALL ON transactions FROM app_user"))
    op.execute(
        sa.text(
            "DROP POLICY IF EXISTS transactions_tenant_isolation ON transactions"
        )
    )
    op.execute(sa.text("ALTER TABLE transactions DISABLE ROW LEVEL SECURITY"))

    op.drop_index("ix_transactions_created_at", table_name="transactions")
    op.drop_index("ix_transactions_type", table_name="transactions")
    op.drop_index("ix_transactions_status", table_name="transactions")
    op.drop_index(
        "ix_transactions_external_transaction_id", table_name="transactions"
    )
    op.drop_index("ix_transactions_payment_id", table_name="transactions")
    op.drop_index("ix_transactions_office_id", table_name="transactions")

    op.drop_table("transactions")
