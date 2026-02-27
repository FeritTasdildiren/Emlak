"""rls_policies

Revision ID: 002_rls_policies
Revises: 001_initial
Create Date: 2026-02-20

Row-Level Security (RLS) multi-tenant veri izolasyonu:

1. Messages tablosuna office_id eklenir (denormalize — Conversation üzerinden dolaylı erişim
   yerine doğrudan RLS filtresi için).
2. Tüm data-bearing tablolarda ENABLE + FORCE ROW LEVEL SECURITY.
3. tenant_isolation policy: office_id = current_setting('app.current_office_id', true)::uuid
   - missing-ok=true → setting yoksa NULL döner → hiçbir satır eşleşmez → default deny.
4. Properties: ek shared_properties policy (cross-office paylaşım).
5. Users: ek platform_admin_bypass policy (tüm ofislere erişim).

Office tablosu → RLS UYGULANMAZ (tenant root entity).

FORCE ROW LEVEL SECURITY: Table owner bile RLS'e tabi olur.
Bu ekstra güvenlik katmanı, yanlışlıkla superuser bağlantısı ile
veri sızıntısını önler.
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "002_rls_policies"
down_revision: Union[str, None] = "001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# RLS uygulanacak tablolar (offices HARİÇ — tenant root)
RLS_TABLES: list[str] = [
    "customers",
    "properties",
    "conversations",
    "messages",
    "notifications",
    "subscriptions",
    "users",
]


def upgrade() -> None:
    # ================================================================
    # 1. Messages tablosuna office_id ekle (denormalize — RLS için)
    # ================================================================
    # Mevcut veri yok, sadece schema değişikliği.
    # Uygulama katmanında mesaj oluşturulurken Conversation.office_id
    # kopyalanarak set edilecek.
    op.add_column(
        "messages",
        sa.Column(
            "office_id",
            sa.UUID(),
            sa.ForeignKey("offices.id"),
            nullable=True,
            comment="Denormalize ofis ID (RLS için). Conversation'dan kopyalanır.",
        ),
    )
    op.create_index("ix_messages_office_id", "messages", ["office_id"])

    # ================================================================
    # 2. ENABLE + FORCE ROW LEVEL SECURITY
    # ================================================================
    # ENABLE RLS: Policy'ler aktif olur.
    # FORCE RLS: Table owner (superuser dahil) bile RLS'e tabi olur.
    for table in RLS_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
        op.execute(sa.text(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))

    # ================================================================
    # 3. Tenant isolation policies (tüm data-bearing tablolar)
    # ================================================================
    # current_setting('app.current_office_id', true):
    #   - İkinci parametre true = missing-ok
    #   - Setting yoksa → NULL döner
    #   - NULL = uuid karşılaştırması FAIL → hiçbir satır dönmez (default deny)
    #
    # Policy tipi belirtilmemiş → FOR ALL (SELECT + INSERT + UPDATE + DELETE)
    # INSERT/UPDATE için WITH CHECK belirtilmemiş → USING ifadesi kullanılır
    # → Yeni/güncellenen satırların office_id'si mevcut tenant ile eşleşmeli
    for table in RLS_TABLES:
        op.execute(sa.text(
            f"CREATE POLICY tenant_isolation_{table} ON {table} "
            f"USING (office_id = current_setting('app.current_office_id', true)::uuid)"
        ))

    # ================================================================
    # 4. Properties: Cross-office paylaşım policy'si
    # ================================================================
    # Ofisler arası portföy paylaşımı (network visibility).
    # Permissive policy → tenant_isolation ile OR'lanır:
    #   - Kendi ofisinin ilanları (tenant_isolation) VEYA
    #   - Paylaşıma açık network ilanları (shared_properties)
    # Sadece SELECT — başka ofisin ilanını UPDATE/DELETE edemezsin.
    op.execute(sa.text(
        "CREATE POLICY shared_properties ON properties "
        "FOR SELECT "
        "USING (is_shared = true AND share_visibility = 'network')"
    ))

    # ================================================================
    # 5. Users: Platform admin bypass policy
    # ================================================================
    # Platform yöneticileri tüm ofislerdeki kullanıcıları görebilir.
    # Permissive policy → tenant_isolation ile OR'lanır:
    #   - Kendi ofisinin kullanıcıları (tenant_isolation) VEYA
    #   - Platform admin ise tüm kullanıcılar (platform_admin_bypass)
    # current_setting('app.current_user_role', true) TenantMiddleware
    # tarafından SET LOCAL ile ayarlanır.
    op.execute(sa.text(
        "CREATE POLICY platform_admin_bypass ON users "
        "FOR ALL "
        "USING (current_setting('app.current_user_role', true) = 'platform_admin')"
    ))


def downgrade() -> None:
    # --- Özel policy'leri kaldır ---
    op.execute(sa.text("DROP POLICY IF EXISTS platform_admin_bypass ON users"))
    op.execute(sa.text("DROP POLICY IF EXISTS shared_properties ON properties"))

    # --- Tenant isolation policy'lerini kaldır ---
    for table in RLS_TABLES:
        op.execute(sa.text(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}"))

    # --- RLS'i devre dışı bırak ---
    for table in RLS_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))

    # --- Messages.office_id kaldır ---
    op.drop_index("ix_messages_office_id", table_name="messages")
    op.drop_column("messages", "office_id")
