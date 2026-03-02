"""appointments

Revision ID: 025_appointments
Revises: 024_bank_rates_table
Create Date: 2026-03-02

Randevu (Appointment) tablosu:

1. CREATE TABLE appointments — danışman-müşteri randevuları.
2. İndeksler: office+date, office+status, customer_id, property_id, user_id.
3. RLS: tenant isolation policy (office_id bazlı).
4. GRANT: app_user rolüne SELECT, INSERT, UPDATE, DELETE erişimi.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "025_appointments"
down_revision: str | None = "024_bank_rates_table"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ================================================================
    # 1. CREATE TABLE appointments
    # ================================================================
    op.create_table(
        "appointments",
        # ---------- PK ----------
        sa.Column(
            "id",
            sa.UUID(),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        # ---------- Tenant ----------
        sa.Column(
            "office_id",
            sa.UUID(),
            sa.ForeignKey("offices.id", ondelete="RESTRICT"),
            nullable=False,
            comment="Bağlı ofis (tenant) ID",
        ),
        # ---------- Danışman ----------
        sa.Column(
            "user_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            comment="Randevuyu oluşturan danışman ID",
        ),
        # ---------- İlişkili Kayıtlar (Opsiyonel) ----------
        sa.Column(
            "customer_id",
            sa.UUID(),
            sa.ForeignKey("customers.id", ondelete="SET NULL"),
            nullable=True,
            comment="Bağlı müşteri ID (opsiyonel)",
        ),
        sa.Column(
            "property_id",
            sa.UUID(),
            sa.ForeignKey("properties.id", ondelete="SET NULL"),
            nullable=True,
            comment="Bağlı ilan ID (opsiyonel)",
        ),
        # ---------- Randevu Bilgileri ----------
        sa.Column(
            "title",
            sa.String(200),
            nullable=False,
            comment="Randevu başlığı",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Ek açıklama",
        ),
        sa.Column(
            "appointment_date",
            sa.DateTime(timezone=True),
            nullable=False,
            comment="Randevu tarihi ve saati",
        ),
        sa.Column(
            "duration_minutes",
            sa.Integer(),
            server_default=sa.text("30"),
            nullable=False,
            comment="Randevu süresi (dakika)",
        ),
        sa.Column(
            "status",
            sa.String(20),
            server_default=sa.text("'scheduled'"),
            nullable=False,
            comment="Randevu durumu: scheduled, completed, cancelled, no_show",
        ),
        sa.Column(
            "location",
            sa.String(300),
            nullable=True,
            comment="Randevu yeri",
        ),
        sa.Column(
            "notes",
            sa.Text(),
            nullable=True,
            comment="Dahili notlar",
        ),
        # ---------- Timestamps ----------
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
        # ---------- Constraints ----------
        sa.PrimaryKeyConstraint("id"),
    )

    # ================================================================
    # 2. İndeksler
    # ================================================================
    op.create_index(
        "ix_appointments_office_date",
        "appointments",
        ["office_id", "appointment_date"],
    )
    op.create_index(
        "ix_appointments_office_status",
        "appointments",
        ["office_id", "status"],
    )
    op.create_index(
        "ix_appointments_customer_id",
        "appointments",
        ["customer_id"],
    )
    op.create_index(
        "ix_appointments_property_id",
        "appointments",
        ["property_id"],
    )
    op.create_index(
        "ix_appointments_user_id",
        "appointments",
        ["user_id"],
    )

    # ================================================================
    # 3. Row-Level Security (RLS)
    # ================================================================
    op.execute(sa.text("ALTER TABLE appointments ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE appointments FORCE ROW LEVEL SECURITY"))

    # Tenant isolation policy
    op.execute(sa.text(
        "CREATE POLICY appointments_tenant_isolation ON appointments "
        "USING (office_id = current_setting('app.current_office_id', true)::uuid)"
    ))

    # Platform admin bypass policy
    op.execute(sa.text(
        "CREATE POLICY appointments_platform_admin_bypass ON appointments "
        "USING (current_setting('app.current_user_role', true) = 'platform_admin')"
    ))

    # ================================================================
    # 4. GRANT
    # ================================================================
    op.execute(sa.text(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON appointments TO app_user"
    ))


def downgrade() -> None:
    # --- GRANT kaldır ---
    op.execute(sa.text("REVOKE ALL ON appointments FROM app_user"))

    # --- RLS policy kaldır ---
    op.execute(sa.text(
        "DROP POLICY IF EXISTS appointments_platform_admin_bypass ON appointments"
    ))
    op.execute(sa.text(
        "DROP POLICY IF EXISTS appointments_tenant_isolation ON appointments"
    ))

    # --- RLS devre dışı bırak ---
    op.execute(sa.text("ALTER TABLE appointments DISABLE ROW LEVEL SECURITY"))

    # --- İndeksleri kaldır ---
    op.drop_index("ix_appointments_user_id", table_name="appointments")
    op.drop_index("ix_appointments_property_id", table_name="appointments")
    op.drop_index("ix_appointments_customer_id", table_name="appointments")
    op.drop_index("ix_appointments_office_status", table_name="appointments")
    op.drop_index("ix_appointments_office_date", table_name="appointments")

    # --- Tabloyu kaldır ---
    op.drop_table("appointments")
