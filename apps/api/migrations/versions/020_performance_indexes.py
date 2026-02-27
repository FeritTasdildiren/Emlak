"""performance_indexes

Revision ID: 020_performance_indexes
Revises: 019_showcase_model
Create Date: 2026-02-27

Performans optimizasyonu — composite ve partial indeksler.
TASK-155: Backend Performans Faz 1

İndeksler:
1. ix_subscriptions_office_status_created — Abonelik plan sorguları (7+ sorgu noktası)
2. ix_prediction_logs_office_created — Değerleme geçmişi + anomaly detection
3. ix_notifications_user_active — Bildirim sorguları (partial: is_deleted=false)
4. ix_area_district_lower — Bölge analizi case-insensitive arama
5. ix_deprem_district — Deprem riski ilçe araması
6. ix_properties_agent_id — Danışmana göre ilan listesi
7. ix_customers_office_created — Müşteri listesi (office + sıralama)

NOT: RLS/FORCE ROW LEVEL SECURITY bu migration'da gerekli DEĞİL (sadece indeks).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "020_performance_indexes"
down_revision: str | None = "019_showcase_model"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ================================================================
    # YÜKSEK — 7+ sorgu noktasında kullanılıyor
    # ================================================================

    # Abonelik plan sorguları: office_id + status + created_at
    # Kullanım: _get_plan_type(), kota kontrolü, subscription lookup
    op.create_index(
        "ix_subscriptions_office_status_created",
        "subscriptions",
        ["office_id", "status", "created_at"],
    )

    # Değerleme geçmişi + anomaly detection: office_id + created_at
    # Kullanım: list_valuations, _get_usage_count, anomaly_service
    op.create_index(
        "ix_prediction_logs_office_created",
        "prediction_logs",
        ["office_id", "created_at"],
    )

    # Bildirim sorguları: user_id + is_read (sadece silinmemiş kayıtlar)
    # Partial index — is_deleted=false satırları çok daha az, indeks küçük kalır
    op.create_index(
        "ix_notifications_user_active",
        "notifications",
        ["user_id", "is_read"],
        postgresql_where=sa.text("is_deleted = false"),
    )

    # ================================================================
    # ORTA
    # ================================================================

    # Bölge analizi: case-insensitive ilçe araması
    op.create_index(
        "ix_area_district_lower",
        "area_analyses",
        [sa.text("lower(district)")],
    )

    # Deprem riski: ilçe bazlı sorgular
    op.create_index(
        "ix_deprem_district",
        "deprem_risks",
        ["district"],
    )

    # İlan listesi: danışmana göre filtreleme
    op.create_index(
        "ix_properties_agent_id",
        "properties",
        ["agent_id"],
    )

    # Müşteri listesi: ofis + oluşturulma tarihi sıralaması
    op.create_index(
        "ix_customers_office_created",
        "customers",
        ["office_id", "created_at"],
    )


def downgrade() -> None:
    # Ters sırada kaldır
    op.drop_index("ix_customers_office_created", table_name="customers")
    op.drop_index("ix_properties_agent_id", table_name="properties")
    op.drop_index("ix_deprem_district", table_name="deprem_risks")
    op.drop_index("ix_area_district_lower", table_name="area_analyses")
    op.drop_index("ix_notifications_user_active", table_name="notifications")
    op.drop_index("ix_prediction_logs_office_created", table_name="prediction_logs")
    op.drop_index("ix_subscriptions_office_status_created", table_name="subscriptions")
