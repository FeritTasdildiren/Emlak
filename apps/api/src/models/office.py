"""
Emlak Teknoloji Platformu - Office Model

Emlak ofisi (tenant) entity'si.
Multi-tenant mimaride birincil izolasyon birimi.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from geoalchemy2 import Geography
from sqlalchemy import Boolean, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

if TYPE_CHECKING:
    from src.models.user import User


class Office(BaseModel):
    """
    Emlak ofisi — platform'un tenant birimi.

    Her ofis bağımsız bir müşteri havuzu, ilan portföyü ve
    kullanıcı (agent) kadrosuna sahiptir.
    """

    __tablename__ = "offices"

    # ---------- Temel Bilgiler ----------
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="Ofis adı"
    )
    slug: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, comment="URL-friendly benzersiz tanımlayıcı"
    )

    # ---------- İletişim ----------
    logo_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="Logo dosya URL'i (MinIO)"
    )
    phone: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Ofis telefonu"
    )
    email: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Ofis e-posta adresi"
    )
    address: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="Açık adres"
    )

    # ---------- Konum ----------
    location = mapped_column(
        Geography("POINT", srid=4326, spatial_index=True),
        nullable=True,
        comment="Ofis konum koordinatları (GEOGRAPHY POINT)",
    )
    city: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="İl"
    )
    district: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="İlçe"
    )

    # ---------- Resmi Bilgiler ----------
    tax_number: Mapped[str | None] = mapped_column(
        String(20), nullable=True, comment="Vergi numarası"
    )

    # ---------- Durum ----------
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true"),
        comment="Ofis aktif mi",
    )

    # ---------- İlişkiler ----------
    users: Mapped[list[User]] = relationship(
        "User", back_populates="office", lazy="raise",
    )
