"""showcase_model

Revision ID: 019_showcase_model
Revises: 018_usage_quota_expand
Create Date: 2026-02-25

Danışman Portfolyo Vitrini (Showcase) tablosu:

1. CREATE TABLE showcases — vitrin verileri.
2. İndeksler: slug (unique), office+agent (composite), is_active (partial).
3. RLS: tenant isolation policy (office_id bazlı).
4. GRANT: app_user rolüne erişim.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "019_showcase_model"
down_revision: str | None = "018_usage_quota_expand"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ================================================================
    # 1. CREATE TABLE showcases
    # ================================================================
    op.create_table(
        "showcases",
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
            "agent_id",
            sa.UUID(),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
            comment="Vitrin sahibi danışman ID",
        ),
        # ---------- Vitrin Bilgileri ----------
        sa.Column(
            "title",
            sa.String(200),
            nullable=False,
            comment="Vitrin başlığı",
        ),
        sa.Column(
            "slug",
            sa.String(100),
            nullable=False,
            comment="Public URL slug (ör: ali-yilmaz-kadikoy)",
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Vitrin açıklaması",
        ),
        # ---------- Seçili İlanlar ----------
        sa.Column(
            "selected_properties",
            sa.dialects.postgresql.JSONB(),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
            comment="Seçili ilan UUID listesi (JSON array)",
        ),
        # ---------- Danışman İletişim ----------
        sa.Column(
            "agent_photo_url",
            sa.String(500),
            nullable=True,
            comment="Danışman profil fotoğrafı URL",
        ),
        sa.Column(
            "agent_phone",
            sa.String(20),
            nullable=True,
            comment="Danışman telefon numarası",
        ),
        sa.Column(
            "agent_email",
            sa.String(200),
            nullable=True,
            comment="Danışman e-posta adresi",
        ),
        sa.Column(
            "agent_whatsapp",
            sa.String(20),
            nullable=True,
            comment="Danışman WhatsApp numarası",
        ),
        # ---------- Tema & Ayarlar ----------
        sa.Column(
            "theme",
            sa.String(20),
            server_default=sa.text("'default'"),
            nullable=False,
            comment="Vitrin teması: default, modern, classic vb.",
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
            comment="Vitrin aktif mi",
        ),
        sa.Column(
            "settings",
            sa.dialects.postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
            comment="Ek vitrin ayarları (JSON)",
        ),
        # ---------- İstatistik ----------
        sa.Column(
            "views_count",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Görüntülenme sayısı",
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
    # Slug UNIQUE index
    op.create_index(
        "ix_showcases_slug",
        "showcases",
        ["slug"],
        unique=True,
    )

    # Composite index: ofis + danışman
    op.create_index(
        "ix_showcases_office_agent",
        "showcases",
        ["office_id", "agent_id"],
    )

    # Partial index: sadece aktif vitrinler
    op.create_index(
        "ix_showcases_is_active",
        "showcases",
        ["is_active"],
        postgresql_where=sa.text("is_active = true"),
    )

    # ================================================================
    # 3. Row-Level Security (RLS)
    # ================================================================
    # ENABLE + FORCE RLS
    op.execute(sa.text("ALTER TABLE showcases ENABLE ROW LEVEL SECURITY"))
    op.execute(sa.text("ALTER TABLE showcases FORCE ROW LEVEL SECURITY"))

    # Tenant isolation policy
    op.execute(sa.text(
        "CREATE POLICY showcases_tenant_isolation ON showcases "
        "USING (office_id = current_setting('app.current_office_id', true)::uuid)"
    ))

    # ================================================================
    # 4. GRANT
    # ================================================================
    op.execute(sa.text("GRANT ALL ON showcases TO app_user"))


def downgrade() -> None:
    # --- GRANT kaldır ---
    op.execute(sa.text("REVOKE ALL ON showcases FROM app_user"))

    # --- RLS policy kaldır ---
    op.execute(sa.text("DROP POLICY IF EXISTS showcases_tenant_isolation ON showcases"))

    # --- RLS devre dışı bırak ---
    op.execute(sa.text("ALTER TABLE showcases DISABLE ROW LEVEL SECURITY"))

    # --- İndeksleri kaldır ---
    op.drop_index("ix_showcases_is_active", table_name="showcases")
    op.drop_index("ix_showcases_office_agent", table_name="showcases")
    op.drop_index("ix_showcases_slug", table_name="showcases")

    # --- Tabloyu kaldır ---
    op.drop_table("showcases")
