"""
Emlak Teknoloji Platformu - Dashboard Router

Ofis bazli ozet istatistik endpoint'i.

Prefix: /api/v1/dashboard
Guvenlik: JWT zorunlu (ActiveUser dependency).
Tenant izolasyonu: office_id JWT'den otomatik alinir.

Endpoint'ler:
    GET /dashboard/stats -> Ofis ozet istatistikleri (JWT)
"""

from __future__ import annotations

from datetime import UTC, datetime

import structlog
from fastapi import APIRouter
from sqlalchemy import case, func, select

from src.dependencies import DBSession
from src.models.customer import Customer
from src.models.notification import Notification
from src.models.prediction_log import PredictionLog
from src.models.property import Property
from src.modules.auth.dependencies import ActiveUser
from src.modules.dashboard.schemas import (
    CustomersByStatus,
    DashboardStatsResponse,
    RecentActivity,
)

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/dashboard",
    tags=["dashboard"],
)


@router.get(
    "/stats",
    response_model=DashboardStatsResponse,
    summary="Ofis ozet istatistikleri",
    description=(
        "Dashboard icin ofise ait portfoy, musteri, degerleme, "
        "bildirim sayilari ve son aktiviteleri dondurur."
    ),
)
async def get_dashboard_stats(
    db: DBSession,
    current_user: ActiveUser,
) -> DashboardStatsResponse:
    """
    Ofis ozet istatistiklerini dondurur.

    - portfolio_count: Toplam ilan sayisi
    - active_portfolio_count: status='active' olan ilan sayisi
    - customer_count: Toplam musteri sayisi
    - customers_by_status: Lead durumuna gore dagilimlari
    - valuation_count_this_month: Bu ayki degerleme sayisi
    - unread_notification_count: Okunmamis bildirim sayisi
    - recent_activities: Son 10 aktivite (PredictionLog + Customer + Property)
    """
    office_id = current_user.office_id

    # --- 1. Portfoy sayilari (tek sorgu, conditional count) ---
    portfolio_stmt = select(
        func.count(Property.id).label("total"),
        func.count(
            case((Property.status == "active", Property.id))
        ).label("active"),
    ).where(Property.office_id == office_id)
    portfolio_result = await db.execute(portfolio_stmt)
    portfolio_row = portfolio_result.one()
    portfolio_count = portfolio_row.total
    active_portfolio_count = portfolio_row.active

    # --- 2. Musteri sayilari (status bazli tek sorgu) ---
    customer_stmt = select(
        func.count(Customer.id).label("total"),
        func.count(
            case((Customer.lead_status == "cold", Customer.id))
        ).label("cold"),
        func.count(
            case((Customer.lead_status == "warm", Customer.id))
        ).label("warm"),
        func.count(
            case((Customer.lead_status == "hot", Customer.id))
        ).label("hot"),
        func.count(
            case((Customer.lead_status == "converted", Customer.id))
        ).label("converted"),
        func.count(
            case((Customer.lead_status == "lost", Customer.id))
        ).label("lost"),
    ).where(Customer.office_id == office_id)
    customer_result = await db.execute(customer_stmt)
    customer_row = customer_result.one()

    # --- 3. Bu ayki degerleme sayisi ---
    now = datetime.now(UTC)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    valuation_stmt = select(
        func.count(PredictionLog.id),
    ).where(
        PredictionLog.office_id == office_id,
        PredictionLog.created_at >= month_start,
    )
    valuation_result = await db.execute(valuation_stmt)
    valuation_count_this_month = valuation_result.scalar_one()

    # --- 4. Okunmamis bildirim sayisi ---
    notif_stmt = select(
        func.count(Notification.id),
    ).where(
        Notification.user_id == current_user.id,
        Notification.is_read.is_(False),
    )
    notif_result = await db.execute(notif_stmt)
    unread_notification_count = notif_result.scalar_one()

    # --- 5. Son aktiviteler (3 tablodan UNION-like, Python merge) ---
    activities: list[RecentActivity] = []

    # Son degerleme kayitlari
    val_stmt = (
        select(PredictionLog.created_at, PredictionLog.input_data)
        .where(PredictionLog.office_id == office_id)
        .order_by(PredictionLog.created_at.desc())
        .limit(10)
    )
    val_result = await db.execute(val_stmt)
    for row in val_result.all():
        district = row.input_data.get("district", "") if row.input_data else ""
        activities.append(
            RecentActivity(
                type="valuation",
                title=f"Degerleme: {district}" if district else "Yeni degerleme",
                timestamp=row.created_at,
            )
        )

    # Son eklenen musteriler
    cust_stmt = (
        select(Customer.created_at, Customer.full_name)
        .where(Customer.office_id == office_id)
        .order_by(Customer.created_at.desc())
        .limit(10)
    )
    cust_result = await db.execute(cust_stmt)
    for row in cust_result.all():
        activities.append(
            RecentActivity(
                type="customer",
                title=f"Yeni musteri: {row.full_name}",
                timestamp=row.created_at,
            )
        )

    # Son eklenen ilanlar
    prop_stmt = (
        select(Property.created_at, Property.title)
        .where(Property.office_id == office_id)
        .order_by(Property.created_at.desc())
        .limit(10)
    )
    prop_result = await db.execute(prop_stmt)
    for row in prop_result.all():
        activities.append(
            RecentActivity(
                type="property",
                title=f"Yeni ilan: {row.title}",
                timestamp=row.created_at,
            )
        )

    # Tum aktiviteleri zamana gore sirala ve ilk 10'u al
    activities.sort(key=lambda a: a.timestamp, reverse=True)
    recent_activities = activities[:10]

    return DashboardStatsResponse(
        portfolio_count=portfolio_count,
        active_portfolio_count=active_portfolio_count,
        customer_count=customer_row.total,
        customers_by_status=CustomersByStatus(
            cold=customer_row.cold,
            warm=customer_row.warm,
            hot=customer_row.hot,
            converted=customer_row.converted,
            lost=customer_row.lost,
        ),
        valuation_count_this_month=valuation_count_this_month,
        unread_notification_count=unread_notification_count,
        recent_activities=recent_activities,
    )
