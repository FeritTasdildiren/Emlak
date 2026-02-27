"""app_user_role

Revision ID: 003_app_user_role
Revises: 002_rls_policies
Create Date: 2026-02-20

Application DB kullanıcısı oluşturur (RLS-enforced sorgular için).

app_user rolü:
- LOGIN yetkili (uygulama bu kullanıcı ile bağlanır)
- superuser DEĞİL (RLS bypass edemez)
- table owner DEĞİL (FORCE RLS sayesinde owner bile bypass edemez,
  ama app_user zaten owner değil — çift güvenlik)
- SELECT, INSERT, UPDATE, DELETE on ALL TABLES
- USAGE, SELECT on ALL SEQUENCES
- ALTER DEFAULT PRIVILEGES ile gelecek tablolar da otomatik yetkilendirilir

Şifre: APP_DB_PASSWORD environment variable'ından okunur.
"""

import os
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "003_app_user_role"
down_revision: Union[str, None] = "002_rls_policies"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # 1. app_user rolü oluştur
    # ================================================================
    # Şifre environment variable'dan okunur — migration'a hardcode edilmez.
    # DO $$ ... END $$ bloğu ile IF NOT EXISTS kontrolü (idempotent).
    password = os.environ.get("APP_DB_PASSWORD", "change_me_app_user_password")
    # SQL injection koruması: tek tırnak escape
    safe_password = password.replace("'", "''")

    op.execute(sa.text(
        "DO $$ "
        "BEGIN "
        "    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'app_user') THEN "
        f"        CREATE ROLE app_user LOGIN PASSWORD '{safe_password}'; "
        "    END IF; "
        "END "
        "$$"
    ))

    # ================================================================
    # 2. Schema erişimi
    # ================================================================
    op.execute(sa.text("GRANT USAGE ON SCHEMA public TO app_user"))

    # ================================================================
    # 3. Mevcut tablo ve sequence yetkileri
    # ================================================================
    op.execute(sa.text(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_user"
    ))
    op.execute(sa.text(
        "GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_user"
    ))

    # ================================================================
    # 4. Gelecek tablolar için default privileges
    # ================================================================
    # Migration'ı çalıştıran kullanıcı (genellikle postgres) tarafından
    # oluşturulacak yeni tablolar da otomatik olarak yetkilendirilir.
    op.execute(sa.text(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO app_user"
    ))
    op.execute(sa.text(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "GRANT USAGE, SELECT ON SEQUENCES TO app_user"
    ))


def downgrade() -> None:
    # --- Default privileges geri al ---
    op.execute(sa.text(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM app_user"
    ))
    op.execute(sa.text(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        "REVOKE USAGE, SELECT ON SEQUENCES FROM app_user"
    ))

    # --- Mevcut tablo/sequence yetkileri geri al ---
    op.execute(sa.text("REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM app_user"))
    op.execute(sa.text("REVOKE ALL ON ALL TABLES IN SCHEMA public FROM app_user"))

    # --- Schema erişimi geri al ---
    op.execute(sa.text("REVOKE USAGE ON SCHEMA public FROM app_user"))

    # --- Rolü kaldır ---
    op.execute(sa.text("DROP ROLE IF EXISTS app_user"))
