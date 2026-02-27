"""payment_table

Revision ID: 004_payment_table
Revises: 003_app_user_role
Create Date: 2026-02-20

Ödeme (payments) tablosunu oluşturur ve subscriptions tablosuna
ödeme takip alanları ekler.

Değişiklikler:
1. payments tablosu oluşturulur (tüm kolonlar + indeksler)
2. subscriptions tablosuna 3 yeni kolon eklenir:
   - last_payment_at: Son başarılı ödeme zamanı
   - next_payment_at: Sonraki ödeme tarihi
   - payment_failed_count: Ardışık başarısız ödeme sayısı
3. RLS: ENABLE + FORCE + tenant_isolation policy
4. app_user GRANT: SELECT, INSERT, UPDATE, DELETE
5. external_id UNIQUE index: Duplicate ödeme engeli
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_payment_table"
down_revision: Union[str, None] = "003_app_user_role"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # 1. payments tablosu oluştur
    # ================================================================
    op.create_table(
        "payments",
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
            "subscription_id", sa.UUID(),
            nullable=False,
            comment="Bağlı abonelik ID",
        ),
        sa.Column(
            "amount", sa.Numeric(10, 2),
            nullable=False,
            comment="Ödeme tutarı",
        ),
        sa.Column(
            "currency", sa.String(3),
            server_default=sa.text("'TRY'"),
            nullable=False,
            comment="Para birimi (ISO 4217)",
        ),
        sa.Column(
            "status", sa.String(20),
            nullable=False,
            comment="Ödeme durumu: pending, processing, completed, failed, refunded",
        ),
        sa.Column(
            "payment_method", sa.String(30),
            nullable=False,
            comment="Ödeme yöntemi: credit_card, bank_transfer, iyzico",
        ),
        sa.Column(
            "external_id", sa.String(100),
            nullable=True,
            comment="Ödeme sağlayıcı benzersiz ID (duplicate ödeme engeli)",
        ),
        sa.Column(
            "external_status", sa.String(50),
            nullable=True,
            comment="Ödeme sağlayıcı durum kodu",
        ),
        sa.Column(
            "paid_at", sa.DateTime(timezone=True),
            nullable=True,
            comment="Ödeme tamamlanma zamanı",
        ),
        sa.Column(
            "refunded_at", sa.DateTime(timezone=True),
            nullable=True,
            comment="İade zamanı",
        ),
        sa.Column(
            "metadata", postgresql.JSONB(),
            server_default=sa.text("'{}'::jsonb"),
            nullable=False,
            comment="Ek bilgiler JSON (sağlayıcı yanıtları, kart bilgisi vb.)",
        ),
        sa.Column(
            "error_message", sa.String(),
            nullable=True,
            comment="Başarısız ödeme hata mesajı",
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
        sa.ForeignKeyConstraint(
            ["subscription_id"], ["subscriptions.id"], ondelete="RESTRICT"
        ),
    )

    # ================================================================
    # 2. İndeksler
    # ================================================================
    # office_id: Tenant bazlı sorgular için
    op.create_index("ix_payments_office_id", "payments", ["office_id"])
    # subscription_id: Abonelik bazlı ödeme geçmişi için
    op.create_index("ix_payments_subscription_id", "payments", ["subscription_id"])
    # external_id: UNIQUE — aynı ödemenin tekrar kaydını engeller
    op.create_index(
        "ix_payments_external_id", "payments", ["external_id"],
        unique=True,
        postgresql_where=sa.text("external_id IS NOT NULL"),
    )
    # status: Durum bazlı filtreleme (pending ödemeleri listeleme vb.)
    op.create_index("ix_payments_status", "payments", ["status"])

    # ================================================================
    # 3. subscriptions tablosuna ödeme takip alanları ekle
    # ================================================================
    op.add_column(
        "subscriptions",
        sa.Column(
            "last_payment_at", sa.DateTime(timezone=True),
            nullable=True,
            comment="Son başarılı ödeme zamanı",
        ),
    )
    op.add_column(
        "subscriptions",
        sa.Column(
            "next_payment_at", sa.DateTime(timezone=True),
            nullable=True,
            comment="Sonraki ödeme tarihi",
        ),
    )
    op.add_column(
        "subscriptions",
        sa.Column(
            "payment_failed_count", sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
            comment="Ardışık başarısız ödeme sayısı",
        ),
    )

    # ================================================================
    # 4. RLS: ENABLE + FORCE + tenant_isolation policy
    # ================================================================
    # ENABLE RLS: Policy'ler aktif olur
    op.execute(sa.text("ALTER TABLE payments ENABLE ROW LEVEL SECURITY"))
    # FORCE RLS: Table owner (superuser dahil) bile RLS'e tabi olur
    op.execute(sa.text("ALTER TABLE payments FORCE ROW LEVEL SECURITY"))
    # Tenant isolation: Sadece kendi ofisinin ödemelerini görebilir
    op.execute(sa.text(
        "CREATE POLICY tenant_isolation_payments ON payments "
        "USING (office_id = current_setting('app.current_office_id', true)::uuid)"
    ))

    # ================================================================
    # 5. app_user GRANT
    # ================================================================
    # app_user rolüne payments tablosu erişim yetkileri.
    # NOT: 003_app_user_role migration'ındaki ALTER DEFAULT PRIVILEGES sayesinde
    # bu adım teknik olarak gereksiz olabilir (migration sahibi aynıysa).
    # Ancak explicit grant, farklı owner senaryolarında güvenlik sağlar.
    op.execute(sa.text(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON payments TO app_user"
    ))


def downgrade() -> None:
    # --- app_user GRANT geri al ---
    op.execute(sa.text("REVOKE ALL ON payments FROM app_user"))

    # --- RLS policy ve kuralları kaldır ---
    op.execute(sa.text("DROP POLICY IF EXISTS tenant_isolation_payments ON payments"))
    op.execute(sa.text("ALTER TABLE payments DISABLE ROW LEVEL SECURITY"))

    # --- subscriptions ödeme takip alanlarını kaldır ---
    op.drop_column("subscriptions", "payment_failed_count")
    op.drop_column("subscriptions", "next_payment_at")
    op.drop_column("subscriptions", "last_payment_at")

    # --- İndeksleri kaldır ---
    op.drop_index("ix_payments_status", table_name="payments")
    op.drop_index("ix_payments_external_id", table_name="payments")
    op.drop_index("ix_payments_subscription_id", table_name="payments")
    op.drop_index("ix_payments_office_id", table_name="payments")

    # --- payments tablosunu kaldır ---
    op.drop_table("payments")
