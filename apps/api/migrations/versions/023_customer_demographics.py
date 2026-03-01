"""customer_demographics

Revision ID: 022_customer_demographics
Revises: 021_transaction_audit_log
Create Date: 2026-03-01

Müşteri tablosuna demografik bilgi kolonları ekleme:
- gender: Cinsiyet (erkek, kadin, belirtilmemis)
- age_range: Yaş aralığı (18-25, 26-35, 36-45, 46-55, 56-65, 65+)
- profession: Meslek (serbest giriş)
- family_size: Aile büyüklüğü (integer)

NOT: RLS policy'lerine dokunulmadı — mevcut tenant_isolation_customers policy
tüm kolonları kapsar (satır bazlı filtreleme).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic
revision: str = "023_customer_demographics"
down_revision: str = "022_property_form_standardization"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "customers",
        sa.Column(
            "gender",
            sa.String(10),
            nullable=True,
            comment="Cinsiyet: erkek, kadin, belirtilmemis",
        ),
    )
    op.add_column(
        "customers",
        sa.Column(
            "age_range",
            sa.String(10),
            nullable=True,
            comment="Yaş aralığı: 18-25, 26-35, 36-45, 46-55, 56-65, 65+",
        ),
    )
    op.add_column(
        "customers",
        sa.Column(
            "profession",
            sa.String(50),
            nullable=True,
            comment="Meslek",
        ),
    )
    op.add_column(
        "customers",
        sa.Column(
            "family_size",
            sa.Integer(),
            nullable=True,
            comment="Aile büyüklüğü",
        ),
    )


def downgrade() -> None:
    op.drop_column("customers", "family_size")
    op.drop_column("customers", "profession")
    op.drop_column("customers", "age_range")
    op.drop_column("customers", "gender")
