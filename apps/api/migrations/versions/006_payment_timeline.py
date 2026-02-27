"""payment_timeline

Revision ID: 006_payment_timeline
Revises: 005_outbox_inbox_events
Create Date: 2026-02-20

Payment Timeline + Refund/Void alanları:

1. initiated_at   — ödeme başlatılma zamanı (DateTime TZ nullable)
2. confirmed_at   — ödeme onaylanma zamanı (DateTime TZ nullable)
3. refund_amount   — iade tutarı (Numeric 10,2 nullable)
4. refund_reason   — iade nedeni (String 255 nullable)
5. void_at         — ödeme iptal (void) zamanı (DateTime TZ nullable)
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "006_payment_timeline"
down_revision: Union[str, None] = "005_outbox_inbox_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ================================================================
    # 1. Timeline alanları
    # ================================================================
    op.add_column(
        "payments",
        sa.Column(
            "initiated_at", sa.DateTime(timezone=True),
            nullable=True,
            comment="Ödeme başlatılma zamanı",
        ),
    )
    op.add_column(
        "payments",
        sa.Column(
            "confirmed_at", sa.DateTime(timezone=True),
            nullable=True,
            comment="Ödeme onaylanma zamanı",
        ),
    )

    # ================================================================
    # 2. Refund alanları
    # ================================================================
    op.add_column(
        "payments",
        sa.Column(
            "refund_amount", sa.Numeric(10, 2),
            nullable=True,
            comment="İade tutarı (kısmi iade destekler)",
        ),
    )
    op.add_column(
        "payments",
        sa.Column(
            "refund_reason", sa.String(255),
            nullable=True,
            comment="İade nedeni açıklaması",
        ),
    )

    # ================================================================
    # 3. Void alanı
    # ================================================================
    op.add_column(
        "payments",
        sa.Column(
            "void_at", sa.DateTime(timezone=True),
            nullable=True,
            comment="Ödeme iptal (void) zamanı",
        ),
    )


def downgrade() -> None:
    op.drop_column("payments", "void_at")
    op.drop_column("payments", "refund_reason")
    op.drop_column("payments", "refund_amount")
    op.drop_column("payments", "confirmed_at")
    op.drop_column("payments", "initiated_at")
