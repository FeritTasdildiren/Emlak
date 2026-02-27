"""customer_update_match_model

Revision ID: 016_customer_update_match_model
Revises: 015_area_demographics
Create Date: 2026-02-22

Customer tablosu güncellemeleri:
1. Yeni kolonlar: agent_id, customer_type, desired_area_min/max, tags, lead_status, last_contact_at
2. Kolon rename: preferred_rooms→desired_rooms, preferred_districts→desired_districts, status→lead_status
3. Mevcut 'active' lead_status değerlerini 'warm' olarak güncelle
4. Index rename + yeni indexler

property_customer_matches tablosu:
1. CREATE TABLE + indexler + UNIQUE constraint
2. RLS: ENABLE + FORCE + tenant_isolation policy
3. app_user GRANT: SELECT, INSERT, UPDATE, DELETE
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "016_customer_update_match_model"
down_revision: str | None = "015_area_demographics"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ================================================================
    # 1. Customer tablosu — Yeni kolonlar
    # ================================================================
    op.add_column(
        "customers",
        sa.Column(
            "agent_id", sa.UUID(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            comment="Atanan danışman (agent) ID",
        ),
    )
    op.add_column(
        "customers",
        sa.Column(
            "customer_type", sa.String(20),
            nullable=False, server_default=sa.text("'buyer'"),
            comment="Müşteri tipi: buyer, seller, renter, landlord",
        ),
    )
    op.add_column(
        "customers",
        sa.Column(
            "desired_area_min", sa.Integer(),
            nullable=True,
            comment="Minimum aranan alan (m²)",
        ),
    )
    op.add_column(
        "customers",
        sa.Column(
            "desired_area_max", sa.Integer(),
            nullable=True,
            comment="Maksimum aranan alan (m²)",
        ),
    )
    op.add_column(
        "customers",
        sa.Column(
            "tags", sa.dialects.postgresql.JSONB(),
            nullable=False, server_default=sa.text("'[]'::jsonb"),
            comment="Müşteri etiketleri JSON dizisi",
        ),
    )
    op.add_column(
        "customers",
        sa.Column(
            "last_contact_at", sa.DateTime(timezone=True),
            nullable=True,
            comment="Son iletişim zamanı",
        ),
    )

    # ================================================================
    # 2. Customer tablosu — Kolon rename
    # ================================================================
    op.execute(sa.text(
        "ALTER TABLE customers RENAME COLUMN preferred_rooms TO desired_rooms"
    ))
    op.execute(sa.text(
        "ALTER TABLE customers RENAME COLUMN preferred_districts TO desired_districts"
    ))
    op.execute(sa.text(
        "ALTER TABLE customers RENAME COLUMN status TO lead_status"
    ))

    # desired_rooms String(50) olarak genişlet (eski String(20) idi)
    op.execute(sa.text(
        "ALTER TABLE customers ALTER COLUMN desired_rooms TYPE varchar(50)"
    ))

    # lead_status server_default güncelle
    op.execute(sa.text(
        "ALTER TABLE customers ALTER COLUMN lead_status SET DEFAULT 'warm'"
    ))

    # ================================================================
    # 3. Customer tablosu — Mevcut 'active' değerlerini 'warm' yap
    # ================================================================
    op.execute(sa.text(
        "UPDATE customers SET lead_status = 'warm' WHERE lead_status = 'active'"
    ))

    # ================================================================
    # 4. Customer tablosu — Index rename + yeni indexler
    # ================================================================
    op.execute(sa.text(
        "ALTER INDEX IF EXISTS ix_customers_office_id_status "
        "RENAME TO ix_customers_office_id_lead_status"
    ))
    op.create_index("ix_customers_agent_id", "customers", ["agent_id"])
    op.create_index("ix_customers_customer_type", "customers", ["customer_type"])

    # ================================================================
    # 5. property_customer_matches tablosu — CREATE TABLE
    # ================================================================
    op.create_table(
        "property_customer_matches",
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
            "property_id", sa.UUID(),
            sa.ForeignKey("properties.id", ondelete="CASCADE"),
            nullable=False,
            comment="Eşleştirilen ilan ID",
        ),
        sa.Column(
            "customer_id", sa.UUID(),
            sa.ForeignKey("customers.id", ondelete="CASCADE"),
            nullable=False,
            comment="Eşleştirilen müşteri ID",
        ),
        sa.Column(
            "score", sa.Float(),
            nullable=False,
            comment="Eşleşme skoru (0-100)",
        ),
        sa.Column(
            "status", sa.String(20),
            nullable=False, server_default=sa.text("'pending'"),
            comment="Eşleştirme durumu: pending, interested, passed, contacted, converted",
        ),
        sa.Column(
            "matched_at", sa.DateTime(timezone=True),
            nullable=False, server_default=sa.text("now()"),
            comment="Eşleştirme zamanı",
        ),
        sa.Column(
            "responded_at", sa.DateTime(timezone=True),
            nullable=True,
            comment="Müşteri yanıt zamanı",
        ),
        sa.Column(
            "notes", sa.Text(),
            nullable=True,
            comment="Eşleştirme notları",
        ),
        sa.UniqueConstraint(
            "property_id", "customer_id",
            name="uq_matches_property_customer",
        ),
    )

    # ================================================================
    # 6. property_customer_matches — Indexler
    # ================================================================
    op.create_index(
        "ix_matches_office_id_status",
        "property_customer_matches",
        ["office_id", "status"],
    )
    op.create_index(
        "ix_matches_customer_id",
        "property_customer_matches",
        ["customer_id"],
    )

    # ================================================================
    # 7. property_customer_matches — RLS: ENABLE + FORCE + POLICY
    # ================================================================
    op.execute(sa.text(
        "ALTER TABLE property_customer_matches ENABLE ROW LEVEL SECURITY"
    ))
    op.execute(sa.text(
        "ALTER TABLE property_customer_matches FORCE ROW LEVEL SECURITY"
    ))
    op.execute(sa.text(
        "CREATE POLICY tenant_isolation_property_customer_matches "
        "ON property_customer_matches "
        "USING (office_id = current_setting('app.current_office_id', true)::uuid)"
    ))

    # ================================================================
    # 8. property_customer_matches — app_user GRANT
    # ================================================================
    op.execute(sa.text(
        "GRANT SELECT, INSERT, UPDATE, DELETE "
        "ON property_customer_matches TO app_user"
    ))


def downgrade() -> None:
    # --- property_customer_matches: app_user GRANT geri al ---
    op.execute(sa.text(
        "REVOKE ALL ON property_customer_matches FROM app_user"
    ))

    # --- property_customer_matches: RLS geri al ---
    op.execute(sa.text(
        "DROP POLICY IF EXISTS tenant_isolation_property_customer_matches "
        "ON property_customer_matches"
    ))
    op.execute(sa.text(
        "ALTER TABLE property_customer_matches DISABLE ROW LEVEL SECURITY"
    ))

    # --- property_customer_matches: Indexler geri al ---
    op.drop_index("ix_matches_customer_id", table_name="property_customer_matches")
    op.drop_index("ix_matches_office_id_status", table_name="property_customer_matches")

    # --- property_customer_matches: Tablo sil ---
    op.drop_table("property_customer_matches")

    # --- Customer: Indexler geri al ---
    op.drop_index("ix_customers_customer_type", table_name="customers")
    op.drop_index("ix_customers_agent_id", table_name="customers")
    op.execute(sa.text(
        "ALTER INDEX IF EXISTS ix_customers_office_id_lead_status "
        "RENAME TO ix_customers_office_id_status"
    ))

    # --- Customer: lead_status server_default geri al ---
    op.execute(sa.text(
        "ALTER TABLE customers ALTER COLUMN lead_status SET DEFAULT 'active'"
    ))

    # --- Customer: 'warm' değerlerini 'active' yap (rename geri al öncesi) ---
    op.execute(sa.text(
        "UPDATE customers SET lead_status = 'active' WHERE lead_status = 'warm'"
    ))

    # --- Customer: desired_rooms String(20) geri al ---
    op.execute(sa.text(
        "ALTER TABLE customers ALTER COLUMN desired_rooms TYPE varchar(20)"
    ))

    # --- Customer: Kolon rename geri al ---
    op.execute(sa.text(
        "ALTER TABLE customers RENAME COLUMN lead_status TO status"
    ))
    op.execute(sa.text(
        "ALTER TABLE customers RENAME COLUMN desired_districts TO preferred_districts"
    ))
    op.execute(sa.text(
        "ALTER TABLE customers RENAME COLUMN desired_rooms TO preferred_rooms"
    ))

    # --- Customer: Yeni kolonları sil ---
    op.drop_column("customers", "last_contact_at")
    op.drop_column("customers", "tags")
    op.drop_column("customers", "desired_area_max")
    op.drop_column("customers", "desired_area_min")
    op.drop_column("customers", "customer_type")
    op.drop_column("customers", "agent_id")
