"""
Emlak Teknoloji Platformu - Earthquake Risk Router

Deprem risk endpoint'leri.

Prefix: /api/v1/earthquake
Guvenlik: Tum endpoint'ler JWT gerektirir (ActiveUser).
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Query
from sqlalchemy import func, select

from src.core.exceptions import NotFoundError
from src.dependencies import DBSession
from src.models.deprem_risk import DepremRisk
from src.modules.auth.dependencies import ActiveUser
from src.modules.earthquake.building_score import BuildingScoreService
from src.modules.earthquake.schemas import (
    BuildingScoreRequest,
    BuildingScoreResult,
    ConstructionType,
    EarthquakeRiskResponse,
    SoilClass,
)
from src.modules.earthquake.service import calculate_risk_level

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/earthquake",
    tags=["earthquake"],
)


@router.get(
    "/risk/{district}",
    response_model=EarthquakeRiskResponse,
    summary="Ilce deprem riski",
    description=(
        "Belirtilen ilce icin deprem risk bilgilerini dondurur. "
        "PGA, zemin sinifi, fay mesafesi ve risk seviyesi hesaplanir."
    ),
    responses={404: {"description": "Ilce deprem verisi bulunamadi"}},
)
async def get_earthquake_risk(
    district: str,
    db: DBSession,
    user: ActiveUser,
) -> EarthquakeRiskResponse:
    """
    DepremRisk tablosundan ilce bazli deprem risk verisi getirir.

    risk_level PGA degerine gore hesaplanir:
    - pga < 0.1: Dusuk
    - 0.1-0.2: Orta
    - 0.2-0.4: Yuksek
    - > 0.4: Cok Yuksek

    Raises:
        NotFoundError: Ilce deprem verisi bulunamazsa 404.
    """
    stmt = select(DepremRisk).where(
        func.lower(DepremRisk.district) == district.lower(),
        DepremRisk.neighborhood.is_(None),
    )
    result = await db.execute(stmt)
    risk = result.scalar_one_or_none()

    if risk is None:
        raise NotFoundError(resource="Deprem riski", resource_id=district)

    pga = float(risk.pga_value) if risk.pga_value else None

    logger.info(
        "earthquake_risk_fetched",
        district=district,
        risk_score=float(risk.risk_score),
        user_id=str(user.id),
    )

    return EarthquakeRiskResponse(
        city=risk.city,
        district=risk.district,
        risk_score=float(risk.risk_score),
        risk_level=calculate_risk_level(pga),
        pga_value=pga,
        soil_class=risk.soil_class,
        fault_distance_km=(
            float(risk.fault_distance_km) if risk.fault_distance_km else None
        ),
        building_code_era=risk.building_code_era,
    )


@router.get(
    "/building-risk",
    response_model=BuildingScoreResult,
    summary="Bina deprem guvenlik skoru",
    description=(
        "Bina parametrelerine dayali deprem guvenlik skoru hesaplar. "
        "TBDY 2018 referansli. DB'ye gitmez, pure hesaplama endpoint'idir."
    ),
)
async def get_building_risk(
    user: ActiveUser,
    building_age: int = Query(
        ..., ge=0, le=200, description="Bina yasi (yil)"
    ),
    floors: int = Query(
        ..., ge=1, le=100, description="Toplam kat sayisi"
    ),
    soil_class: SoilClass = Query(  # noqa: B008
        ..., description="TBDY 2018 zemin sinifi: ZA, ZB, ZC, ZD, ZE"
    ),
    construction_type: ConstructionType | None = Query(  # noqa: B008
        default=None,
        description="Yapi tipi: betonarme, celik, yigma, ahsap",
    ),
    has_retrofit: bool | None = Query(
        default=None, description="Guclendirme yapilmis mi"
    ),
) -> BuildingScoreResult:
    """
    Bina parametrelerine dayali deprem guvenlik skoru hesaplar.

    Pure hesaplama — veritabanina erismez.
    BuildingScoreService.calculate_score() kullanilir.
    """
    request = BuildingScoreRequest(
        building_age=building_age,
        floors=floors,
        soil_class=soil_class,
        construction_type=construction_type,
        has_retrofit=has_retrofit,
    )

    result = BuildingScoreService.calculate_score(request)

    logger.info(
        "building_risk_calculated",
        building_age=building_age,
        floors=floors,
        soil_class=soil_class.value,
        safety_score=result.safety_score,
        risk_level=result.risk_level.value,
        user_id=str(user.id),
    )

    return result
