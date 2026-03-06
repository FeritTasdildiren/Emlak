"""RLS platform_admin bypass for showcases and properties.

Public endpoint'ler (vitrin public görünümü) platform_admin role ile
tüm tenant verilerine erişebilmeli. Showcases ve properties tablolarında
bu bypass eksikti.

Revision ID: 026_rls_platform_admin_bypass
Revises: 025_appointments
Create Date: 2026-03-06
"""

from alembic import op

revision = "026_rls_platform_admin_bypass"
down_revision = "025_appointments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Showcases: tenant isolation + platform_admin bypass
    op.execute("DROP POLICY IF EXISTS showcases_tenant_isolation ON showcases")
    op.execute("""
        CREATE POLICY showcases_tenant_isolation ON showcases
        USING (
            office_id = current_setting('app.current_office_id', true)::uuid
            OR current_setting('app.current_user_role', true) = 'platform_admin'
        )
    """)

    # Properties: tenant isolation + platform_admin bypass
    op.execute("DROP POLICY IF EXISTS tenant_isolation_properties ON properties")
    op.execute("""
        CREATE POLICY tenant_isolation_properties ON properties
        USING (
            office_id = current_setting('app.current_office_id', true)::uuid
            OR current_setting('app.current_user_role', true) = 'platform_admin'
        )
    """)


def downgrade() -> None:
    # Revert to original policies without platform_admin bypass
    op.execute("DROP POLICY IF EXISTS showcases_tenant_isolation ON showcases")
    op.execute("""
        CREATE POLICY showcases_tenant_isolation ON showcases
        USING (
            office_id = current_setting('app.current_office_id', true)::uuid
        )
    """)

    op.execute("DROP POLICY IF EXISTS tenant_isolation_properties ON properties")
    op.execute("""
        CREATE POLICY tenant_isolation_properties ON properties
        USING (
            office_id = current_setting('app.current_office_id', true)::uuid
        )
    """)
