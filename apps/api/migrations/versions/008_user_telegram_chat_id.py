"""user_telegram_chat_id

Revision ID: 008_user_telegram_chat_id
Revises: 007_notifications_table
Create Date: 2026-02-20

users tablosuna telegram_chat_id kolonu ekler.
Deep link ile hesap baglama mekanizmasi icin kullanilir.

Degisiklikler:
1. telegram_chat_id kolonu eklenir (VARCHAR(50), nullable, unique)
2. Partial unique index olusturulur (NULL degerleri haric)
3. app_user'a UPDATE yetkisi zaten var (001_initial_schema'da verilmis)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "008_user_telegram_chat_id"
down_revision: Union[str, None] = "007_notifications_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # 1. telegram_chat_id kolonu ekle
    # ================================================================
    op.add_column(
        "users",
        sa.Column(
            "telegram_chat_id",
            sa.String(50),
            nullable=True,
            comment="Telegram bot chat ID (deep link ile baglanan)",
        ),
    )

    # ================================================================
    # 2. Partial unique index — NULL degerler haric tutulur
    #    Ayni chat_id birden fazla kullaniciya baglanamaz.
    # ================================================================
    op.execute(sa.text(
        "CREATE UNIQUE INDEX ix_users_telegram_chat_id "
        "ON users (telegram_chat_id) "
        "WHERE telegram_chat_id IS NOT NULL"
    ))


def downgrade() -> None:
    # --- Partial unique index kaldir ---
    op.execute(sa.text(
        "DROP INDEX IF EXISTS ix_users_telegram_chat_id"
    ))

    # --- telegram_chat_id kolonu kaldir ---
    op.drop_column("users", "telegram_chat_id")
