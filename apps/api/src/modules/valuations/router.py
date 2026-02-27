"""
Emlak Teknoloji Platformu - Valuations Router

ML degerleme ve emsal bulma (comparable) endpoint'leri.

Prefix: /api/v1/valuations
Guvenlik: Tum endpoint'ler JWT gerektirir (ActiveUser).
Kota: POST /valuations plan bazli aylik degerleme kotasi uygular.
"""

from __future__ import annotations

import uuid  # noqa: TC003 — FastAPI resolves UUID at runtime
from datetime import datetime  # noqa: TC003 — FastAPI resolves datetime at runtime

import structlog
from fastapi import APIRouter, Query, Request, status
from sqlalchemy import func as sa_func
from sqlalchemy import select

from src.core.exceptions import NotFoundError, QuotaExceededError
from src.core.plan_policy import get_valuation_quota, is_unlimited_plan
from src.core.rate_limit import limiter
from src.dependencies import DBSession
from src.models.prediction_log import PredictionLog
from src.models.subscription import Subscription
from src.modules.audit.audit_service import AuditService
from src.modules.auth.dependencies import ActiveUser
from src.modules.valuations.anomaly_service import check_price_anomaly
from src.modules.valuations.comparable_service import ComparableService
from src.modules.valuations.inference_service import InferenceService
from src.modules.valuations.schemas import (
    ComparableRequest,
    ComparableResponse,
    ComparableResult,
    ValuationDetailResponse,
    ValuationListItem,
    ValuationListResponse,
    ValuationRequest,
    ValuationResponse,
)

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/valuations",
    tags=["valuations"],
)


# =====================================================================
# Kota kontrol yardimcilari
# =====================================================================
# NOT: TASK-082 paralel calisiyordu. quota_service.py ve usage_quota.py
# modelleri henuz mevcut olmayabilir. Asagida try/except ile import
# denenir; yoksa fallback olarak dogrudan Subscription + PredictionLog
# uzerinden kota hesabi yapilir.
# =====================================================================

try:
    from src.modules.valuations.quota_service import QuotaService  # TASK-082

    _QUOTA_SERVICE_AVAILABLE = True
except ImportError:
    _QUOTA_SERVICE_AVAILABLE = False


async def _get_plan_type(db, office_id: str) -> str:
    """Ofis'in aktif abonelik planini dondurur. Bulunamazsa 'starter' varsayar."""
    stmt = (
        select(Subscription.plan_type)
        .where(
            Subscription.office_id == office_id,
            Subscription.status.in_(["active", "trial"]),
        )
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    plan = result.scalar_one_or_none()
    return plan if plan else "starter"


async def _get_usage_count(db, office_id: str) -> int:
    """
    Ofis'in bu ayki degerleme kullanimini sayar.

    TASK-082 quota_service mevcutsa onu kullanir; yoksa PredictionLog'dan sayar.
    """
    if _QUOTA_SERVICE_AVAILABLE:
        svc = QuotaService(db)
        return await svc.get_current_usage(office_id)

    # Fallback: PredictionLog tablosundan bu ayin sayisi
    stmt = select(sa_func.count(PredictionLog.id)).where(
        PredictionLog.office_id == office_id,
        sa_func.date_trunc("month", PredictionLog.created_at)
        == sa_func.date_trunc("month", sa_func.now()),
    )
    result = await db.execute(stmt)
    return result.scalar_one() or 0


async def _increment_usage(db, office_id: str) -> None:
    """
    Degerleme sonrasi kota kullanimini arttirir.

    TASK-082 quota_service mevcutsa onu kullanir; yoksa no-op
    (PredictionLog zaten InferenceService icinde kaydediliyor).
    """
    if _QUOTA_SERVICE_AVAILABLE:
        svc = QuotaService(db)
        await svc.increment(office_id)


async def _check_and_get_quota(
    db,
    office_id: str,
) -> tuple[str, int, int]:
    """
    Kota kontrolu yapar, (plan_type, quota_limit, used) dondurur.

    Raises:
        QuotaExceededError: Kota asildiginda.
    """
    plan_type = await _get_plan_type(db, office_id)

    # Elite plan sinirsiz — kontrol atla
    if is_unlimited_plan(plan_type):
        return plan_type, -1, 0

    quota_limit = get_valuation_quota(plan_type)
    used = await _get_usage_count(db, office_id)

    if used >= quota_limit:
        logger.warning(
            "valuation_quota_exceeded",
            office_id=office_id,
            plan=plan_type,
            limit=quota_limit,
            used=used,
        )
        raise QuotaExceededError(
            limit=quota_limit,
            used=used,
            plan=plan_type,
        )

    return plan_type, quota_limit, used


# =====================================================================
# Endpoints
# =====================================================================


@router.post(
    "",
    response_model=ValuationResponse,
    status_code=status.HTTP_200_OK,
    summary="ML ile mulk degerleme",
    description=(
        "LightGBM modeli ile konut fiyat tahmini yapar. "
        "Tahmin sonucu otomatik olarak prediction_logs tablosuna kaydedilir. "
        "Plan bazli aylik kota uygulanir (Elite plan sinirsiz)."
    ),
    responses={
        429: {
            "description": "Aylik degerleme kotasi asildi veya rate limit asildi",
            "content": {
                "application/json": {
                    "example": {
                        "type": "quota_exceeded",
                        "title": "Too Many Requests",
                        "status": 429,
                        "detail": "Aylik degerleme kotaniz doldu.",
                        "limit": 50,
                        "used": 50,
                        "plan": "starter",
                        "upgrade_url": "/pricing",
                    }
                }
            },
        }
    },
)
@limiter.limit("30/minute")
async def create_valuation(
    request: Request,
    body: ValuationRequest,
    db: DBSession,
    user: ActiveUser,
) -> ValuationResponse:
    """
    ML model ile fiyat tahmini endpoint'i — kota kontrollu.

    Akis:
        1. Kota kontrolu (plan bazli)
        2. InferenceService singleton'dan model al
        3. Input verisini model'e gonder
        4. Tahmin sonucunu PredictionLog'a kaydet (ayni transaction)
        5. Emsal mulkleri bul (adaptive radius)
        6. Kota kullanimi artir
        7. ValuationResponse olarak dondur (comparables + kota bilgisi)
    """
    # 1. Kota kontrolu
    plan_type, quota_limit, used = await _check_and_get_quota(
        db=db, office_id=str(user.office_id)
    )

    # 2. ML tahmin
    inference = InferenceService.get_instance()

    result = await inference.predict(
        input_data=body.to_model_input(),
        session=db,
        office_id=str(user.office_id),
    )

    # 3. Emsal mulkleri bul (adaptive radius ile)
    model_input = body.to_model_input()
    comparable_svc = ComparableService(db)
    comparables_raw = await comparable_svc.find_comparables_enriched(
        district=body.district,
        property_type=body.property_type,
        net_sqm=body.net_sqm,
        room_count=body.room_count,
        building_age=body.building_age,
        estimated_price=result["estimated_price"],
        lat=model_input.get("lat"),
        lon=model_input.get("lon"),
        limit=5,
        min_comparables=3,
    )

    comparables = [ComparableResult(**c) for c in comparables_raw]

    # 4. Anomali tespiti (basarisiz olursa degerleme yine doner)
    anomaly_warning: str | None = None
    try:
        anomaly_result = await check_price_anomaly(
            predicted_price=float(result["estimated_price"]),
            district=body.district,
            net_sqm=body.net_sqm,
            session=db,
        )
        if anomaly_result.is_anomaly:
            anomaly_warning = anomaly_result.anomaly_reason
    except Exception:
        logger.warning(
            "anomaly_check_failed",
            prediction_id=result["prediction_id"],
            district=body.district,
            exc_info=True,
        )

    # 5. Kota kullanimi artir
    await _increment_usage(db=db, office_id=str(user.office_id))

    # 6. Kota bilgisi hesapla (used artik artti, +1 ekliyoruz)
    quota_remaining = -1 if quota_limit == -1 else max(0, quota_limit - (used + 1))

    logger.info(
        "valuation_created",
        prediction_id=result["prediction_id"],
        district=body.district,
        net_sqm=body.net_sqm,
        estimated_price=result["estimated_price"],
        latency_ms=result["latency_ms"],
        user_id=str(user.id),
        plan=plan_type,
        comparables_count=len(comparables),
        quota_remaining=quota_remaining,
        anomaly_warning=anomaly_warning is not None,
    )

    # KVKK Audit: Degerleme olusturma kaydi
    await AuditService.log_action(
        db=db,
        user_id=user.id,
        office_id=user.office_id,
        action="CREATE",
        entity_type="PredictionLog",
        entity_id=result.get("prediction_id"),
        new_value={
            "district": body.district,
            "net_sqm": body.net_sqm,
            "estimated_price": result["estimated_price"],
        },
        request=request,
    )

    return ValuationResponse(
        **result,
        comparables=comparables,
        quota_remaining=quota_remaining,
        quota_limit=quota_limit,
        anomaly_warning=anomaly_warning,
    )


@router.post(
    "/comparables",
    response_model=ComparableResponse,
    summary="Emsal mulk bul",
    description=(
        "Belirtilen ozelliklere gore benzer mulkleri bulur. "
        "PostGIS mesafe hesaplama ve benzerlik skoru algoritmasi kullanir."
    ),
)
async def find_comparables(
    body: ComparableRequest,
    db: DBSession,
    user: ActiveUser,
) -> ComparableResponse:
    """
    Emsal mulk arama endpoint'i.

    Akis:
        1. ComparableService ile emsal mulkleri bul
        2. Ilce istatistiklerini getir
        3. ComparableResponse olarak dondur
    """
    service = ComparableService(db)

    comparables = await service.find_comparables(
        district=body.district,
        property_type=body.property_type,
        net_sqm=body.net_sqm,
        room_count=body.room_count,
        building_age=body.building_age,
        lat=body.lat,
        lon=body.lon,
    )

    area_stats = await service.get_area_stats(district=body.district)

    logger.info(
        "comparables_found",
        district=body.district,
        property_type=body.property_type,
        total_found=len(comparables),
        user_id=str(user.id),
    )

    return ComparableResponse(
        comparables=comparables,
        area_stats=area_stats,
        total_found=len(comparables),
    )


# =====================================================================
# GET Endpoints — Degerleme gecmisi ve detay
# =====================================================================


@router.get(
    "",
    response_model=ValuationListResponse,
    summary="Degerleme gecmisi listesi",
    description=(
        "Ofise ait degerleme gecmisini sayfalanmis olarak listeler. "
        "Siralama: created_at DESC."
    ),
)
async def list_valuations(
    db: DBSession,
    user: ActiveUser,
    limit: int = Query(default=20, ge=1, le=100, description="Sayfa basina kayit"),
    offset: int = Query(default=0, ge=0, description="Baslangic indeksi"),
    date_from: datetime | None = Query(  # noqa: B008
        default=None, description="Baslangic tarihi (ISO 8601)"
    ),
    date_to: datetime | None = Query(  # noqa: B008
        default=None, description="Bitis tarihi (ISO 8601)"
    ),
) -> ValuationListResponse:
    """
    Ofise ait degerleme gecmisini listeler.

    Akis:
        1. PredictionLog'dan office_id filtreleme
        2. Opsiyonel tarih araligi filtresi
        3. Sayfalama (limit + offset)
        4. created_at DESC siralama
    """
    office_id = str(user.office_id)

    # Temel filtreler
    filters = [PredictionLog.office_id == office_id]
    if date_from is not None:
        filters.append(PredictionLog.created_at >= date_from)
    if date_to is not None:
        filters.append(PredictionLog.created_at <= date_to)

    # Toplam kayit sayisi
    count_stmt = select(sa_func.count(PredictionLog.id)).where(*filters)
    count_result = await db.execute(count_stmt)
    total = count_result.scalar_one() or 0

    # Sayfali liste sorgusu
    list_stmt = (
        select(PredictionLog)
        .where(*filters)
        .order_by(PredictionLog.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(list_stmt)
    rows = result.scalars().all()

    items = [
        ValuationListItem(
            id=str(row.id),
            predicted_price=int(row.output_data.get("estimated_price", 0)),
            confidence_low=int(row.output_data.get("min_price", 0)),
            confidence_high=int(row.output_data.get("max_price", 0)),
            created_at=row.created_at,
            model_version=row.model_version,
        )
        for row in rows
    ]

    logger.info(
        "valuations_listed",
        office_id=office_id,
        total=total,
        returned=len(items),
        user_id=str(user.id),
    )

    return ValuationListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{valuation_id}",
    response_model=ValuationDetailResponse,
    summary="Degerleme detayi",
    description="Belirtilen ID'ye ait degerlemenin tam detayini dondurur.",
    responses={404: {"description": "Degerleme bulunamadi"}},
)
async def get_valuation(
    valuation_id: uuid.UUID,
    db: DBSession,
    user: ActiveUser,
) -> ValuationDetailResponse:
    """
    PredictionLog'dan tek bir degerlemenin tam detayini getirir.

    Raises:
        NotFoundError: Kayit bulunamazsa 404.
    """
    stmt = select(PredictionLog).where(
        PredictionLog.id == valuation_id,
        PredictionLog.office_id == str(user.office_id),
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()

    if row is None:
        raise NotFoundError(resource="Degerleme", resource_id=str(valuation_id))

    return ValuationDetailResponse(
        id=str(row.id),
        predicted_price=int(row.output_data.get("estimated_price", 0)),
        confidence_low=int(row.output_data.get("min_price", 0)),
        confidence_high=int(row.output_data.get("max_price", 0)),
        confidence=row.confidence,
        model_version=row.model_version,
        latency_ms=row.latency_ms,
        input_features=row.input_data,
        output_data=row.output_data,
        created_at=row.created_at,
    )


@router.get(
    "/{valuation_id}/comparables",
    response_model=list[ComparableResult],
    summary="Degerleme emsal listesi",
    description=(
        "Bir degerlemenin input ozelliklerine gore emsal mulkleri bulur. "
        "ComparableService find_comparables_enriched() kullanir."
    ),
    responses={404: {"description": "Degerleme bulunamadi"}},
)
async def get_valuation_comparables(
    valuation_id: uuid.UUID,
    db: DBSession,
    user: ActiveUser,
) -> list[ComparableResult]:
    """
    Belirtilen degerlemenin emsallerini getirir.

    Akis:
        1. PredictionLog'dan degerleme kaydini bul
        2. Input verisinden emsal arama parametrelerini cikar
        3. ComparableService ile emsalleri bul
        4. ComparableResult listesi olarak dondur

    Raises:
        NotFoundError: Kayit bulunamazsa 404.
    """
    # 1. Degerleme kaydini getir
    stmt = select(PredictionLog).where(
        PredictionLog.id == valuation_id,
        PredictionLog.office_id == str(user.office_id),
    )
    result = await db.execute(stmt)
    row = result.scalar_one_or_none()

    if row is None:
        raise NotFoundError(resource="Degerleme", resource_id=str(valuation_id))

    # 2. Input verisinden parametreleri cikar
    input_data = row.input_data
    estimated_price = int(row.output_data.get("estimated_price", 0))

    # 3. ComparableService ile emsal bul
    comparable_svc = ComparableService(db)
    comparables_raw = await comparable_svc.find_comparables_enriched(
        district=input_data.get("district", ""),
        property_type=input_data.get("property_type", ""),
        net_sqm=float(input_data.get("net_sqm", 0)),
        room_count=int(input_data.get("room_count", 1)),
        building_age=int(input_data.get("building_age", 0)),
        estimated_price=estimated_price,
        lat=input_data.get("lat"),
        lon=input_data.get("lon"),
        limit=5,
        min_comparables=3,
    )

    comparables = [ComparableResult(**c) for c in comparables_raw]

    logger.info(
        "valuation_comparables_fetched",
        valuation_id=str(valuation_id),
        comparables_count=len(comparables),
        user_id=str(user.id),
    )

    return comparables
