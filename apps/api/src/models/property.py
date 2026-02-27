"""
Emlak Teknoloji Platformu - Property Model

Emlak ilanı entity'si — platformun ana veri modeli.
"""

from __future__ import annotations

import uuid

from geoalchemy2 import Geography
from sqlalchemy import Boolean, ForeignKey, Index, Integer, Numeric, String, Text, text
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel, TenantMixin


class Property(BaseModel, TenantMixin):
    """
    Emlak ilanı.

    Temel portföy birimi — konum, fiyat, özellikler ve fotoğraflar.
    Full-text search için search_vector (TSVECTOR) alanı içerir.
    PostGIS GEOGRAPHY tipi ile coğrafi sorgular desteklenir.
    """

    __tablename__ = "properties"
    __table_args__ = (
        # Composite B-tree indeksler
        Index("ix_properties_office_status_listing", "office_id", "status", "listing_type"),
        Index("ix_properties_price", "price"),
        Index("ix_properties_city_district", "city", "district"),
        # GIN indeksler
        Index("ix_properties_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_properties_features", "features", postgresql_using="gin"),
    )

    # ---------- Tenant ----------
    office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("offices.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Bağlı ofis (tenant) ID",
    )

    # ---------- Danışman ----------
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        comment="Sorumlu danışman ID",
    )

    # ---------- İlan Bilgileri ----------
    title: Mapped[str] = mapped_column(
        String(300), nullable=False, comment="İlan başlığı"
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="İlan açıklaması"
    )
    property_type: Mapped[str] = mapped_column(
        String(30), nullable=False,
        comment="Emlak tipi: daire, villa, arsa, dükkan, ofis vb.",
    )
    listing_type: Mapped[str] = mapped_column(
        String(10), nullable=False,
        comment="İlan tipi: sale (satılık), rent (kiralık)",
    )

    # ---------- Fiyat ----------
    price: Mapped[float] = mapped_column(
        Numeric(15, 2), nullable=False, comment="Fiyat"
    )
    currency: Mapped[str] = mapped_column(
        String(3), nullable=False, default="TRY",
        server_default=text("'TRY'"),
        comment="Para birimi (ISO 4217)",
    )

    # ---------- Özellikler ----------
    rooms: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Oda sayısı (ör: 3+1)"
    )
    gross_area: Mapped[float | None] = mapped_column(
        Numeric(8, 2), nullable=True, comment="Brüt alan (m²)"
    )
    net_area: Mapped[float | None] = mapped_column(
        Numeric(8, 2), nullable=True, comment="Net alan (m²)"
    )
    floor_number: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Bulunduğu kat"
    )
    total_floors: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Toplam kat sayısı"
    )
    building_age: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="Bina yaşı"
    )
    heating_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="Isıtma tipi"
    )

    # ---------- Konum ----------
    address: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Açık adres"
    )
    location = mapped_column(
        Geography("POINT", srid=4326, spatial_index=True),
        nullable=False,
        comment="Konum koordinatları (GEOGRAPHY POINT)",
    )
    city: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="İl"
    )
    district: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="İlçe"
    )
    neighborhood: Mapped[str | None] = mapped_column(
        String(100), nullable=True, comment="Mahalle"
    )

    # ---------- Ek Veriler (JSON) ----------
    features: Mapped[dict] = mapped_column(
        JSONB, nullable=False, server_default=text("'{}'::jsonb"),
        comment="Ek özellikler (balkon, otopark, vb.) JSON",
    )
    photos: Mapped[list] = mapped_column(
        JSONB, nullable=False, server_default=text("'[]'::jsonb"),
        comment="Fotoğraf URL listesi JSON",
    )

    # ---------- Durum & Paylaşım ----------
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active",
        server_default=text("'active'"),
        comment="İlan durumu: active, passive, sold, rented",
    )
    is_shared: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false"),
        comment="Ofisler arası paylaşıma açık mı",
    )
    share_visibility: Mapped[str] = mapped_column(
        String(20), nullable=False, default="private",
        server_default=text("'private'"),
        comment="Paylaşım görünürlüğü: private, shared, public",
    )

    # ---------- İstatistik ----------
    views_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0"),
        comment="Görüntülenme sayısı",
    )

    # ---------- Full-Text Search ----------
    search_vector: Mapped[str | None] = mapped_column(
        TSVECTOR, nullable=True,
        comment="PostgreSQL full-text search vektörü (trigger ile güncellenir)",
    )

    # ---------- İlişkiler ----------
    office = relationship("Office", lazy="selectin")
    agent = relationship("User", lazy="selectin")
