"""
Emlak Teknoloji Platformu - BankRate Model

Banka konut kredisi faiz oranlarini temsil eden tablo.

Mimari Karar:
    - RLS YOKTUR — bank_rates global tablo, tenant-bagimsiz.
      Tum ofisler ayni faiz oranlarini gorur.
    - BaseModel kullanilMAZ — UUID PK yerine BigInteger autoincrement.
      Tenant-bagimsiz referans verisi icin basit PK yeterli.
    - updated_at: Son oran guncelleme zamani (server_default=now())
    - update_source: Guncelleme kaynagi (manual | seed | tcmb_proxy)

Referans: TASK-193
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, Index, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class BankRate(Base):
    """Banka konut kredisi faiz orani."""

    __tablename__ = "bank_rates"

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    bank_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True,
    )
    annual_rate: Mapped[datetime] = mapped_column(
        Numeric(5, 2),
        nullable=False,
    )
    min_term: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=12,
    )
    max_term: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=120,
    )
    min_amount: Mapped[datetime] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=100_000,
    )
    max_amount: Mapped[datetime] = mapped_column(
        Numeric(15, 2),
        nullable=False,
        default=10_000_000,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    update_source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="manual",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    __table_args__ = (
        Index("idx_bank_rates_active_updated", "is_active", updated_at.desc()),
    )

    def __repr__(self) -> str:
        return f"<BankRate(id={self.id}, bank={self.bank_name}, rate={self.annual_rate}%)>"
