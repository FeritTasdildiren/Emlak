"""property_form_standardization

Revision ID: 022_property_form_standardization
Revises: 021_transaction_audit_log
Create Date: 2026-03-01

TASK-189: Property Form Standardizasyon
- ADD COLUMN bathroom_count (Integer, nullable)
- ADD COLUMN furniture_status (String(20), nullable)
- ADD COLUMN building_type (String(20), nullable)
- ADD COLUMN facade (String(20), nullable)

RLS'e dokunulmaz — mevcut properties policy'si yeni nullable kolonlari kapsar.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "022_property_form_standardization"
down_revision: str | None = "021_transaction_audit_log"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "properties",
        sa.Column(
            "bathroom_count",
            sa.Integer(),
            nullable=True,
            comment="Banyo sayisi",
        ),
    )
    op.add_column(
        "properties",
        sa.Column(
            "furniture_status",
            sa.String(20),
            nullable=True,
            comment="Esya durumu: bos, esyali, yari_esyali",
        ),
    )
    op.add_column(
        "properties",
        sa.Column(
            "building_type",
            sa.String(20),
            nullable=True,
            comment="Yapi tipi: betonarme, celik, ahsap, prefabrik, tas, tugla",
        ),
    )
    op.add_column(
        "properties",
        sa.Column(
            "facade",
            sa.String(20),
            nullable=True,
            comment="Cephe yonu: kuzey, guney, dogu, bati vb.",
        ),
    )


def downgrade() -> None:
    op.drop_column("properties", "facade")
    op.drop_column("properties", "building_type")
    op.drop_column("properties", "furniture_status")
    op.drop_column("properties", "bathroom_count")
