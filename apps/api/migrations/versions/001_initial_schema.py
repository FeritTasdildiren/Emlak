"""initial_schema

Revision ID: 001_initial
Revises:
Create Date: 2026-02-20

Tüm core entity tablolarını oluşturur:
- offices (tenant)
- users
- subscriptions
- customers
- properties (GEOGRAPHY + TSVECTOR)
- conversations
- messages
- notifications
"""

from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ---------- PostGIS Extension ----------
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")

    # ========== 1. OFFICES ==========
    op.create_table(
        "offices",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False, comment="Ofis adı"),
        sa.Column("slug", sa.String(100), nullable=False, comment="URL-friendly benzersiz tanımlayıcı"),
        sa.Column("logo_url", sa.String(500), nullable=True, comment="Logo dosya URL'i (MinIO)"),
        sa.Column("phone", sa.String(20), nullable=True, comment="Ofis telefonu"),
        sa.Column("email", sa.String(255), nullable=True, comment="Ofis e-posta adresi"),
        sa.Column("address", sa.Text(), nullable=True, comment="Açık adres"),
        sa.Column(
            "location",
            geoalchemy2.types.Geography("POINT", srid=4326, spatial_index=True),
            nullable=True,
            comment="Ofis konum koordinatları (GEOGRAPHY POINT)",
        ),
        sa.Column("city", sa.String(100), nullable=False, comment="İl"),
        sa.Column("district", sa.String(100), nullable=False, comment="İlçe"),
        sa.Column("tax_number", sa.String(20), nullable=True, comment="Vergi numarası"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False, comment="Ofis aktif mi"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )

    # ========== 2. USERS ==========
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, comment="E-posta adresi"),
        sa.Column("phone", sa.String(20), nullable=True, comment="Telefon numarası"),
        sa.Column("password_hash", sa.String(255), nullable=False, comment="Bcrypt hash'lenmiş şifre"),
        sa.Column("full_name", sa.String(150), nullable=False, comment="Ad soyad"),
        sa.Column("avatar_url", sa.String(500), nullable=True, comment="Profil fotoğrafı URL'i"),
        sa.Column("role", sa.String(20), nullable=False, comment="Kullanıcı rolü: agent, office_admin, office_owner, platform_admin"),
        sa.Column("office_id", sa.UUID(), nullable=False, comment="Bağlı ofis (tenant) ID"),
        sa.Column("telegram_id", sa.BigInteger(), nullable=True, comment="Telegram kullanıcı ID"),
        sa.Column("whatsapp_phone", sa.String(20), nullable=True, comment="WhatsApp telefon numarası"),
        sa.Column("preferred_channel", sa.String(20), server_default=sa.text("'telegram'"), nullable=False, comment="Tercih edilen iletişim kanalı"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False, comment="Hesap aktif mi"),
        sa.Column("is_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False, comment="E-posta doğrulanmış mı"),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True, comment="Son giriş zamanı"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["office_id"], ["offices.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_office_id", "users", ["office_id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index(
        "ix_users_telegram_id", "users", ["telegram_id"],
        unique=True, postgresql_where=sa.text("telegram_id IS NOT NULL"),
    )

    # ========== 3. SUBSCRIPTIONS ==========
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("office_id", sa.UUID(), nullable=False, comment="Bağlı ofis (tenant) ID"),
        sa.Column("plan_type", sa.String(20), nullable=False, comment="Plan tipi: starter, pro, elite"),
        sa.Column("status", sa.String(20), nullable=False, comment="Abonelik durumu: trial, active, past_due, cancelled"),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=False, comment="Başlangıç tarihi"),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True, comment="Bitiş tarihi"),
        sa.Column("trial_end_date", sa.DateTime(timezone=True), nullable=True, comment="Deneme süresi bitiş tarihi"),
        sa.Column("monthly_price", sa.Numeric(10, 2), nullable=False, comment="Aylık ücret (TRY)"),
        sa.Column("features", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False, comment="Plan özellikleri JSON"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["office_id"], ["offices.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_subscriptions_office_id", "subscriptions", ["office_id"])

    # ========== 4. CUSTOMERS ==========
    op.create_table(
        "customers",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("office_id", sa.UUID(), nullable=False, comment="Bağlı ofis (tenant) ID"),
        sa.Column("full_name", sa.String(200), nullable=False, comment="Ad soyad"),
        sa.Column("phone", sa.String(20), nullable=True, comment="Telefon numarası"),
        sa.Column("email", sa.String(255), nullable=True, comment="E-posta adresi"),
        sa.Column("notes", sa.Text(), nullable=True, comment="Danışman notları"),
        sa.Column("budget_min", sa.Numeric(15, 2), nullable=True, comment="Minimum bütçe (TRY)"),
        sa.Column("budget_max", sa.Numeric(15, 2), nullable=True, comment="Maksimum bütçe (TRY)"),
        sa.Column("preferred_type", sa.String(30), nullable=True, comment="Tercih edilen emlak tipi"),
        sa.Column("preferred_rooms", sa.String(20), nullable=True, comment="Tercih edilen oda sayısı"),
        sa.Column("preferred_districts", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False, comment="Tercih edilen ilçeler JSON dizisi"),
        sa.Column("status", sa.String(20), server_default=sa.text("'active'"), nullable=False, comment="Müşteri durumu"),
        sa.Column("source", sa.String(50), nullable=True, comment="Müşteri kaynağı (referans, ilan, vb.)"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["office_id"], ["offices.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_customers_office_id_status", "customers", ["office_id", "status"])

    # ========== 5. PROPERTIES ==========
    op.create_table(
        "properties",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("office_id", sa.UUID(), nullable=False, comment="Bağlı ofis (tenant) ID"),
        sa.Column("agent_id", sa.UUID(), nullable=False, comment="Sorumlu danışman ID"),
        sa.Column("title", sa.String(300), nullable=False, comment="İlan başlığı"),
        sa.Column("description", sa.Text(), nullable=True, comment="İlan açıklaması"),
        sa.Column("property_type", sa.String(30), nullable=False, comment="Emlak tipi: daire, villa, arsa, dükkan, ofis vb."),
        sa.Column("listing_type", sa.String(10), nullable=False, comment="İlan tipi: sale (satılık), rent (kiralık)"),
        sa.Column("price", sa.Numeric(15, 2), nullable=False, comment="Fiyat"),
        sa.Column("currency", sa.String(3), server_default=sa.text("'TRY'"), nullable=False, comment="Para birimi (ISO 4217)"),
        sa.Column("rooms", sa.String(20), nullable=True, comment="Oda sayısı (ör: 3+1)"),
        sa.Column("gross_area", sa.Numeric(8, 2), nullable=True, comment="Brüt alan (m²)"),
        sa.Column("net_area", sa.Numeric(8, 2), nullable=True, comment="Net alan (m²)"),
        sa.Column("floor_number", sa.Integer(), nullable=True, comment="Bulunduğu kat"),
        sa.Column("total_floors", sa.Integer(), nullable=True, comment="Toplam kat sayısı"),
        sa.Column("building_age", sa.Integer(), nullable=True, comment="Bina yaşı"),
        sa.Column("heating_type", sa.String(50), nullable=True, comment="Isıtma tipi"),
        sa.Column("address", sa.Text(), nullable=True, comment="Açık adres"),
        sa.Column(
            "location",
            geoalchemy2.types.Geography("POINT", srid=4326, spatial_index=True),
            nullable=False,
            comment="Konum koordinatları (GEOGRAPHY POINT)",
        ),
        sa.Column("city", sa.String(100), nullable=False, comment="İl"),
        sa.Column("district", sa.String(100), nullable=False, comment="İlçe"),
        sa.Column("neighborhood", sa.String(100), nullable=True, comment="Mahalle"),
        sa.Column("features", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False, comment="Ek özellikler JSON"),
        sa.Column("photos", postgresql.JSONB(), server_default=sa.text("'[]'::jsonb"), nullable=False, comment="Fotoğraf URL listesi JSON"),
        sa.Column("status", sa.String(20), server_default=sa.text("'active'"), nullable=False, comment="İlan durumu"),
        sa.Column("is_shared", sa.Boolean(), server_default=sa.text("false"), nullable=False, comment="Ofisler arası paylaşıma açık mı"),
        sa.Column("share_visibility", sa.String(20), server_default=sa.text("'private'"), nullable=False, comment="Paylaşım görünürlüğü"),
        sa.Column("views_count", sa.Integer(), server_default=sa.text("0"), nullable=False, comment="Görüntülenme sayısı"),
        sa.Column("search_vector", postgresql.TSVECTOR(), nullable=True, comment="PostgreSQL full-text search vektörü"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["office_id"], ["offices.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["agent_id"], ["users.id"], ondelete="RESTRICT"),
    )
    # GiST index for location is created automatically by geoalchemy2 spatial_index=True
    op.create_index("ix_properties_office_status_listing", "properties", ["office_id", "status", "listing_type"])
    op.create_index("ix_properties_price", "properties", ["price"])
    op.create_index("ix_properties_city_district", "properties", ["city", "district"])
    op.create_index("ix_properties_search_vector", "properties", ["search_vector"], postgresql_using="gin")
    op.create_index("ix_properties_features", "properties", ["features"], postgresql_using="gin")

    # ========== 6. CONVERSATIONS ==========
    op.create_table(
        "conversations",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("office_id", sa.UUID(), nullable=False, comment="Bağlı ofis (tenant) ID"),
        sa.Column("customer_id", sa.UUID(), nullable=False, comment="Bağlı müşteri ID"),
        sa.Column("channel", sa.String(20), nullable=False, comment="İletişim kanalı: telegram, whatsapp, web"),
        sa.Column("status", sa.String(20), server_default=sa.text("'open'"), nullable=False, comment="Konuşma durumu"),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True, comment="Son mesaj zamanı"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["office_id"], ["offices.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["customer_id"], ["customers.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_conversations_office_id", "conversations", ["office_id"])
    op.create_index("ix_conversations_customer_id", "conversations", ["customer_id"])

    # ========== 7. MESSAGES ==========
    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False, comment="Bağlı konuşma ID"),
        sa.Column("direction", sa.String(10), nullable=False, comment="Mesaj yönü: inbound, outbound"),
        sa.Column("content", sa.Text(), nullable=True, comment="Mesaj metni"),
        sa.Column("message_type", sa.String(20), server_default=sa.text("'text'"), nullable=False, comment="Mesaj tipi"),
        sa.Column("channel", sa.String(20), nullable=False, comment="Kanal: telegram, whatsapp, web"),
        sa.Column("status", sa.String(20), server_default=sa.text("'sent'"), nullable=False, comment="Mesaj durumu"),
        sa.Column("external_id", sa.String(255), nullable=True, comment="Harici platform mesaj ID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_messages_conversation_created", "messages", ["conversation_id", "created_at"])

    # ========== 8. NOTIFICATIONS ==========
    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False, comment="Hedef kullanıcı ID"),
        sa.Column("office_id", sa.UUID(), nullable=False, comment="Bağlı ofis (tenant) ID"),
        sa.Column("type", sa.String(50), nullable=False, comment="Bildirim tipi"),
        sa.Column("title", sa.String(255), nullable=False, comment="Bildirim başlığı"),
        sa.Column("body", sa.Text(), nullable=True, comment="Bildirim detay metni"),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False, comment="Okundu mu"),
        sa.Column("data", postgresql.JSONB(), server_default=sa.text("'{}'::jsonb"), nullable=False, comment="Ek veriler JSON"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["office_id"], ["offices.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_notifications_user_id_is_read", "notifications", ["user_id", "is_read"])
    op.create_index("ix_notifications_office_id", "notifications", ["office_id"])

    # ========== TSVECTOR TRIGGER (Property search_vector auto-update) ==========
    op.execute("""
        CREATE OR REPLACE FUNCTION properties_search_vector_update() RETURNS trigger AS $$
        BEGIN
            NEW.search_vector :=
                setweight(to_tsvector('turkish', COALESCE(NEW.title, '')), 'A') ||
                setweight(to_tsvector('turkish', COALESCE(NEW.description, '')), 'B') ||
                setweight(to_tsvector('turkish', COALESCE(NEW.city, '')), 'C') ||
                setweight(to_tsvector('turkish', COALESCE(NEW.district, '')), 'C') ||
                setweight(to_tsvector('turkish', COALESCE(NEW.neighborhood, '')), 'C');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;

        CREATE TRIGGER trg_properties_search_vector
            BEFORE INSERT OR UPDATE OF title, description, city, district, neighborhood
            ON properties
            FOR EACH ROW
            EXECUTE FUNCTION properties_search_vector_update();
    """)


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_properties_search_vector ON properties")
    op.execute("DROP FUNCTION IF EXISTS properties_search_vector_update()")

    op.drop_table("notifications")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("properties")
    op.drop_table("customers")
    op.drop_table("subscriptions")
    op.drop_table("users")
    op.drop_table("offices")
