"""
Emlak Teknoloji Platformu - Price History Model

Zaman serisi fiyat verileri: bölge/ilçe/şehir bazında aylık fiyat geçmişi.
Platform-level tablo — tenant-specific DEĞİL (office_id YOK).

BIGSERIAL PK kullanılır (UUID yerine) — yüksek hacim tablosu.
Provenance bilgisi source alanı ile takip edilir (data_sources JSONB yerine).
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class PriceHistory(Base):
    """
    Fiyat geçmişi modeli — zaman serisi bölge fiyat verileri.

    BIGSERIAL PK: Yüksek hacim beklentisi (UUID overhead'inden kaçınılır).
    Kaynak izleme: source + provenance_version ile sağlanır.
    Granülerlik: mahalle / ilçe / şehir seviyesinde aylık veriler.
    """

    __tablename__ = "price_histories"

    # ─── Primary Key (BIGSERIAL — yüksek hacim) ─────────────────────
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )

    # ─── Bölge Bilgileri ───────────────────────────────────────────────
    area_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="Granülerlik: neighborhood, district, city",
    )
    area_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        comment="Bölge adı (mahalle/ilçe/şehir ismi)",
    )
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    district: Mapped[str | None] = mapped_column(String(100), nullable=True)
    date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        comment="Veri dönemi (aylık: ayın ilk günü)",
    )

    # ─── Fiyat Verileri ───────────────────────────────────────────────
    avg_price_sqm: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 2),
        comment="Ortalama metrekare birim fiyat (TL)",
    )
    median_price: Mapped[Decimal | None] = mapped_column(
        Numeric(15, 2),
        comment="Medyan satış/kira fiyatı (TL)",
    )
    listing_count: Mapped[int | None] = mapped_column(
        Integer,
        comment="Dönemdeki ilan sayısı",
    )
    transaction_count: Mapped[int | None] = mapped_column(
        Integer,
        comment="Dönemdeki işlem (satış/kiralama) sayısı",
    )

    # ─── PROVENANCE ALANLARI (ADR-0006) ──────────────────────────────
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="Veri kaynağı: TUIK, TCMB, scraping",
    )
    provenance_version: Mapped[str | None] = mapped_column(
        String(50),
        comment="Kaynak veri versiyonu (ör: TUIK-2024-12)",
    )

    # ─── Zaman Damgası ───────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )

    # ─── Constraints & Indexes ───────────────────────────────────────
    __table_args__ = (
        UniqueConstraint(
            "area_type",
            "area_name",
            "city",
            "date",
            "source",
            name="uq_price_area_date_source",
        ),
        Index("ix_price_city_date", "city", "date"),
        Index("ix_price_area_type", "area_type", "area_name"),
    )

    def __repr__(self) -> str:
        return (
            f"<PriceHistory {self.area_type}/{self.area_name} "
            f"{self.date} src={self.source}>"
        )
