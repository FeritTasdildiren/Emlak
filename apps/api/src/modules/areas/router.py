"""
Emlak Teknoloji Platformu - Areas Router

Bolge analiz, m2 fiyat karsilastirma ve fiyat trendi endpoint'leri.

Prefix: /api/v1/areas
Guvenlik: Tum endpoint'ler JWT gerektirir (ActiveUser).
"""

from __future__ import annotations

from datetime import date, timedelta

import structlog
from fastapi import APIRouter, Query
from sqlalchemy import func, select

from src.core.exceptions import NotFoundError, ValidationError
from src.dependencies import DBSession
from src.models.area_analysis import AreaAnalysis
from src.models.price_history import PriceHistory
from src.modules.areas.schemas import (
    AreaDetailResponse,
    CompareAreaItem,
    CompareResponse,
    DemographicsResponse,
    InvestmentMetrics,
    PriceTrendResponse,
    TrendItem,
)
from src.modules.auth.dependencies import ActiveUser
from src.modules.valuations.schemas import AreaPriceComparisonResponse

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/areas",
    tags=["areas"],
)


# ---------- Yardimci fonksiyonlar ----------


def _calculate_investment_metrics(
    avg_sale: float | None,
    avg_rent: float | None,
) -> InvestmentMetrics:
    """Kira verimi ve amortisman hesapla (m2 bazli)."""
    if not avg_sale or not avg_rent or avg_sale <= 0 or avg_rent <= 0:
        return InvestmentMetrics()

    yillik_kira = avg_rent * 12
    kira_verimi = (yillik_kira / avg_sale) * 100
    amortisman = avg_sale / yillik_kira

    return InvestmentMetrics(
        kira_verimi=round(kira_verimi, 2),
        amortisman_yil=round(amortisman, 1),
    )


def _build_age_distribution(area: AreaAnalysis) -> dict[str, float] | None:
    """AreaAnalysis yas grubu yuzde alanlarindan age_distribution dict'i olustur."""
    if area.age_0_14_pct is None:
        return None
    return {
        "0-14": float(area.age_0_14_pct),
        "15-24": float(area.age_15_24_pct) if area.age_15_24_pct else 0.0,
        "25-44": float(area.age_25_44_pct) if area.age_25_44_pct else 0.0,
        "45-64": float(area.age_45_64_pct) if area.age_45_64_pct else 0.0,
        "65+": float(area.age_65_plus_pct) if area.age_65_plus_pct else 0.0,
    }


# ---------- Endpoint'ler ----------


@router.get(
    "/compare",
    response_model=CompareResponse,
    summary="Bolge karsilastirma",
    description=(
        "Birden fazla ilceyi yan yana karsilastirir. "
        "avg_price_sqm_sale, avg_price_sqm_rent, population, investment_score, "
        "transport_score, amenity_score ve yatirim metrikleri dondurulur."
    ),
    responses={
        404: {"description": "Bir veya daha fazla ilce bulunamadi"},
        422: {"description": "Gecersiz parametre (bos veya 3'ten fazla ilce)"},
    },
)
async def compare_areas(
    db: DBSession,
    user: ActiveUser,
    districts: str = Query(
        ...,
        description="Karsilastirilacak ilce adlari (virgullu, maks 3). Ornek: Kadikoy,Besiktas,Uskudar",
    ),
) -> CompareResponse:
    """
    AreaAnalysis tablosundan birden fazla ilceyi karsilastirmali getirir.

    Her ilce icin yatirim metrikleri (kira_verimi, amortisman_yil) hesaplanir.

    Raises:
        ValidationError: Bos liste veya 3'ten fazla ilce gonderildiginde 422.
        NotFoundError: Herhangi bir ilce bulunamazsa 404.
    """
    district_list = [d.strip() for d in districts.split(",") if d.strip()]

    if not district_list:
        raise ValidationError("En az bir ilce adi belirtmelisiniz.")
    if len(district_list) > 3:
        raise ValidationError("En fazla 3 ilce karsilastirabilirsiniz.")

    # Tum ilceleri tek sorguda cek
    stmt = select(AreaAnalysis).where(
        func.lower(AreaAnalysis.district).in_([d.lower() for d in district_list]),
        AreaAnalysis.neighborhood.is_(None),
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    # Bulunan ilceleri dict'e cevir (case-insensitive lookup)
    found: dict[str, AreaAnalysis] = {
        row.district.lower(): row for row in rows
    }

    # Bulunamayan ilceleri kontrol et
    not_found = [d for d in district_list if d.lower() not in found]
    if not_found:
        raise NotFoundError(
            resource="Bolge",
            resource_id=", ".join(not_found),
        )

    # Istenilen siraya gore response olustur
    items: list[CompareAreaItem] = []
    for d in district_list:
        area = found[d.lower()]
        avg_sale = (
            float(area.avg_price_sqm_sale) if area.avg_price_sqm_sale else None
        )
        avg_rent = (
            float(area.avg_price_sqm_rent) if area.avg_price_sqm_rent else None
        )
        items.append(
            CompareAreaItem(
                district=area.district,
                avg_price_sqm_sale=avg_sale,
                avg_price_sqm_rent=avg_rent,
                population=area.population,
                investment_score=(
                    float(area.investment_score) if area.investment_score else None
                ),
                transport_score=(
                    float(area.transport_score) if area.transport_score else None
                ),
                amenity_score=(
                    float(area.amenity_score) if area.amenity_score else None
                ),
                investment_metrics=_calculate_investment_metrics(avg_sale, avg_rent),
            )
        )

    logger.info(
        "area_compare_fetched",
        districts=[d for d in district_list],
        count=len(items),
        user_id=str(user.id),
    )

    return CompareResponse(areas=items, count=len(items))


@router.get(
    "/{district}/price-comparison",
    response_model=AreaPriceComparisonResponse,
    summary="Bolge m2 fiyat karsilastirma",
    description=(
        "Belirtilen ilce icin ortalama m2 fiyati, fiyat trendi "
        "ve yatirim potansiyeli bilgilerini dondurur."
    ),
    responses={404: {"description": "Bolge bulunamadi"}},
)
async def get_area_price_comparison(
    district: str,
    db: DBSession,
    user: ActiveUser,
) -> AreaPriceComparisonResponse:
    """
    AreaAnalysis tablosundan ilce bazli m2 fiyat karsilastirma verisi getirir.

    Raises:
        NotFoundError: Ilce bulunamazsa 404.
    """
    stmt = select(AreaAnalysis).where(
        func.lower(AreaAnalysis.district) == district.lower(),
        AreaAnalysis.neighborhood.is_(None),
    )
    result = await db.execute(stmt)
    area = result.scalar_one_or_none()

    if area is None:
        raise NotFoundError(resource="Bolge", resource_id=district)

    logger.info(
        "area_price_comparison_fetched",
        district=district,
        user_id=str(user.id),
    )

    return AreaPriceComparisonResponse(
        district=area.district,
        avg_price_per_sqm=(
            float(area.avg_price_sqm_sale) if area.avg_price_sqm_sale else None
        ),
        avg_rent_per_sqm=(
            float(area.avg_price_sqm_rent) if area.avg_price_sqm_rent else None
        ),
        trend=float(area.price_trend_6m) if area.price_trend_6m else None,
        listing_count=area.listing_count,
        investment_score=(
            float(area.investment_score) if area.investment_score else None
        ),
    )


@router.get(
    "/{city}/{district}/trends",
    response_model=PriceTrendResponse,
    summary="Ilce fiyat trendi",
    description=(
        "Belirtilen sehir ve ilce icin aylik fiyat trendi verilerini dondurur. "
        "PriceHistory tablosundan district seviyesinde veri cekilir."
    ),
    responses={404: {"description": "Trend verisi bulunamadi"}},
)
async def get_district_price_trends(
    city: str,
    district: str,
    db: DBSession,
    user: ActiveUser,
    months: int = Query(default=6, ge=1, le=24, description="Kac aylik veri (1-24)"),
    type: str = Query(
        default="sale",
        pattern="^(sale|rent)$",
        description="Islem tipi: sale veya rent",
    ),
) -> PriceTrendResponse:
    """
    PriceHistory tablosundan ilce bazli aylik fiyat trendi getirir.

    Raises:
        NotFoundError: Ilce icin trend verisi bulunamazsa 404.
    """
    today = date.today()
    start_date = today - timedelta(days=months * 31)

    stmt = (
        select(PriceHistory)
        .where(
            func.lower(PriceHistory.city) == city.lower(),
            func.lower(PriceHistory.area_name) == district.lower(),
            PriceHistory.area_type == "district",
            PriceHistory.date >= start_date,
        )
        .order_by(PriceHistory.date.asc())
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()

    if not rows:
        raise NotFoundError(resource="Fiyat trendi", resource_id=district)

    trends: list[TrendItem] = []
    for row in rows:
        trends.append(
            TrendItem(
                month=row.date.strftime("%Y-%m"),
                avg_price_sqm=(
                    float(row.avg_price_sqm) if row.avg_price_sqm else None
                ),
                min_price_sqm=None,
                max_price_sqm=None,
                sample_count=row.listing_count,
            )
        )

    # Ilk ve son ay arasindaki degisim yuzdesi
    change_pct: float | None = None
    first_avg = trends[0].avg_price_sqm
    last_avg = trends[-1].avg_price_sqm
    if first_avg and last_avg and first_avg > 0:
        change_pct = round((last_avg - first_avg) / first_avg * 100, 2)

    logger.info(
        "district_price_trends_fetched",
        city=city,
        district=district,
        type=type,
        months=months,
        trend_count=len(trends),
        user_id=str(user.id),
    )

    return PriceTrendResponse(
        district=district,
        type=type,
        months=months,
        trends=trends,
        change_pct=change_pct,
    )


@router.get(
    "/{city}/{district}/demographics",
    response_model=DemographicsResponse,
    summary="Ilce demografik verileri",
    description=(
        "Belirtilen sehir ve ilce icin TUIK kaynakli demografik verileri dondurur. "
        "Yas dagilimi, nufus yogunlugu, hane istatistikleri."
    ),
    responses={404: {"description": "Bolge bulunamadi"}},
)
async def get_district_demographics(
    city: str,
    district: str,
    db: DBSession,
    user: ActiveUser,
) -> DemographicsResponse:
    """
    AreaAnalysis tablosundan ilce bazli demografik veri getirir.

    Raises:
        NotFoundError: Sehir/ilce bulunamazsa 404.
    """
    stmt = select(AreaAnalysis).where(
        func.lower(AreaAnalysis.city) == city.lower(),
        func.lower(AreaAnalysis.district) == district.lower(),
        AreaAnalysis.neighborhood.is_(None),
    )
    result = await db.execute(stmt)
    area = result.scalar_one_or_none()

    if area is None:
        raise NotFoundError(resource="Bolge", resource_id=f"{city}/{district}")

    logger.info(
        "district_demographics_fetched",
        city=city,
        district=district,
        user_id=str(user.id),
    )

    return DemographicsResponse(
        district=area.district,
        population=area.population,
        median_age=float(area.median_age) if area.median_age else None,
        population_density=area.population_density,
        household_count=area.household_count,
        avg_household_size=(
            float(area.avg_household_size) if area.avg_household_size else None
        ),
        age_distribution=_build_age_distribution(area),
    )


@router.get(
    "/{city}/{district}",
    response_model=AreaDetailResponse,
    summary="Ilce detay bilgisi",
    description=(
        "Belirtilen sehir ve ilce icin detayli bolge bilgisi, "
        "fiyat verileri ve yatirim metriklerini dondurur."
    ),
    responses={404: {"description": "Bolge bulunamadi"}},
)
async def get_area_detail(
    city: str,
    district: str,
    db: DBSession,
    user: ActiveUser,
) -> AreaDetailResponse:
    """
    AreaAnalysis tablosundan ilce bazli detay bilgisi getirir.

    Yatirim metrikleri (kira_verimi, amortisman) hesaplanarak dondurulur.

    Raises:
        NotFoundError: Sehir/ilce bulunamazsa 404.
    """
    stmt = select(AreaAnalysis).where(
        func.lower(AreaAnalysis.city) == city.lower(),
        func.lower(AreaAnalysis.district) == district.lower(),
        AreaAnalysis.neighborhood.is_(None),
    )
    result = await db.execute(stmt)
    area = result.scalar_one_or_none()

    if area is None:
        raise NotFoundError(resource="Bolge", resource_id=f"{city}/{district}")

    avg_sale = float(area.avg_price_sqm_sale) if area.avg_price_sqm_sale else None
    avg_rent = float(area.avg_price_sqm_rent) if area.avg_price_sqm_rent else None

    logger.info(
        "area_detail_fetched",
        city=city,
        district=district,
        user_id=str(user.id),
    )

    return AreaDetailResponse(
        city=area.city,
        district=area.district,
        avg_price_sqm_sale=avg_sale,
        avg_price_sqm_rent=avg_rent,
        price_trend_6m=(
            float(area.price_trend_6m) if area.price_trend_6m else None
        ),
        population=area.population,
        listing_count=area.listing_count,
        transport_score=(
            float(area.transport_score) if area.transport_score else None
        ),
        amenity_score=(
            float(area.amenity_score) if area.amenity_score else None
        ),
        investment_score=(
            float(area.investment_score) if area.investment_score else None
        ),
        investment_metrics=_calculate_investment_metrics(avg_sale, avg_rent),
        median_age=float(area.median_age) if area.median_age else None,
        population_density=area.population_density,
        age_distribution=_build_age_distribution(area),
    )
