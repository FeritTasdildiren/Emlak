"""
Emlak Teknoloji Platformu - Dashboard Schemas

Ofis bazli ozet istatistik response modelleri.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class CustomersByStatus(BaseModel):
    """Lead durumuna gore musteri dagilimi."""

    cold: int = Field(default=0, description="Soguk lead sayisi")
    warm: int = Field(default=0, description="Ilik lead sayisi")
    hot: int = Field(default=0, description="Sicak lead sayisi")
    converted: int = Field(default=0, description="Donusen musteri sayisi")
    lost: int = Field(default=0, description="Kaybedilen musteri sayisi")


class RecentActivity(BaseModel):
    """Son aktivite ogesi."""

    type: str = Field(description="Aktivite tipi: valuation, customer, property")
    title: str = Field(description="Aktivite basligi")
    timestamp: datetime = Field(description="Aktivite zamani")


class DashboardStatsResponse(BaseModel):
    """Dashboard istatistik yaniti."""

    portfolio_count: int = Field(description="Toplam portfoy (ilan) sayisi")
    active_portfolio_count: int = Field(description="Aktif ilan sayisi")
    customer_count: int = Field(description="Toplam musteri sayisi")
    customers_by_status: CustomersByStatus = Field(
        description="Lead durumuna gore musteri dagilimi",
    )
    valuation_count_this_month: int = Field(
        description="Bu ayki degerleme sayisi",
    )
    unread_notification_count: int = Field(
        description="Okunmamis bildirim sayisi",
    )
    recent_activities: list[RecentActivity] = Field(
        default_factory=list,
        description="Son 10 aktivite (degerleme + musteri + ilan)",
    )
