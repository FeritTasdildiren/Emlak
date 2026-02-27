"""
Emlak Teknoloji Platformu - Virtual Staging Router

Bos oda fotograflarini yapay zeka ile mobilyali hale getiren endpoint'ler.

Prefix: /api/v1/listings
Guvenlik: virtual-stage ve analyze-room JWT gerektirir (ActiveUser).
           staging-styles public endpoint'tir.

Kota: POST /virtual-stage plan bazli aylik sahneleme kotasi uygular.

Referans: TASK-115 (S8.5 + S8.6)
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, Form, UploadFile, status
from sqlalchemy import select

from src.core.exceptions import QuotaExceededError, ValidationError
from src.dependencies import DBSession  # noqa: TC001 — FastAPI resolves at runtime
from src.listings.staging_schemas import (
    RoomAnalysisResponse,
    StagedImageItem,
    StagingResponse,
    StyleInfo,
    StyleListResponse,
)
from src.listings.staging_service import (
    analyze_room,
    get_available_styles,
    get_model_for_plan,
    get_quality_for_plan,
    staged_image_to_base64,
    virtual_stage,
)
from src.models.subscription import Subscription
from src.modules.auth.dependencies import ActiveUser  # noqa: TC001 — FastAPI runtime
from src.modules.valuations.quota_service import (
    QuotaType,
    check_credit,
    check_quota,
    increment_quota,
    use_credit,
)

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/listings",
    tags=["virtual-staging"],
)


# ---------- Yardimci ----------


async def _get_plan_type(db: DBSession, office_id: str) -> str:
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


# ================================================================
# POST /virtual-stage — JWT zorunlu, multipart
# ================================================================


@router.post(
    "/virtual-stage",
    status_code=status.HTTP_200_OK,
    response_model=StagingResponse,
    summary="Bos oda fotografini sahnele",
    description=(
        "Bos bir oda fotografini secilen tarzda mobilyali hale getirir. "
        "Oda bos degilse 422 doner. Plan bazli kota kontrolu uygulanir."
    ),
)
async def virtual_stage_endpoint(
    image: UploadFile,
    user: ActiveUser,
    db: DBSession,
    style: str = Form(
        ...,
        description="Sahneleme tarzi: modern, klasik, minimalist, skandinav, bohem, endustriyel",
    ),
) -> StagingResponse:
    """
    Virtual staging pipeline endpoint'i.

    Akis:
        1. JWT'den tenant_id + plan_type al
        2. Kota kontrolu (check_quota + check_credit)
        3. Plan bazli model ve kalite belirleme
        4. staging_service.virtual_stage() cagir
        5. Kota sayacini artir
        6. StagingResponse dondur
    """
    office_id = str(user.office_id)

    # 1. Plan tipini al
    plan_type = await _get_plan_type(db, office_id)

    # 2. Kota kontrolu
    is_allowed, used, limit = await check_quota(
        db, user.office_id, plan_type, QuotaType.STAGING,
    )

    if not is_allowed:
        has_credit = await check_credit(
            db, user.office_id, plan_type, QuotaType.STAGING,
        )
        if not has_credit:
            raise QuotaExceededError(
                limit=limit,
                used=used,
                plan=plan_type,
                detail="Aylik sahneleme kotaniz doldu.",
            )
        # Kredi kullan
        await use_credit(db, user.office_id, plan_type, QuotaType.STAGING)

    # 3. Plan bazli model ve kalite
    image_model = get_model_for_plan(plan_type)
    quality = get_quality_for_plan(plan_type)

    # 4. Gorsel oku ve pipeline calistir
    image_bytes = await image.read()
    if not image_bytes:
        raise ValidationError(detail="Gorsel dosyasi bos.")

    try:
        result = await virtual_stage(
            image_bytes,
            style,
            quality=quality,
            image_model=image_model,
        )
    except ValueError as exc:
        raise ValidationError(detail=str(exc)) from exc

    # 5. Kota sayacini artir (kredi ile odenmemisse)
    if is_allowed:
        await increment_quota(db, user.office_id, plan_type, QuotaType.STAGING)

    logger.info(
        "staging_endpoint_success",
        user_id=str(user.id),
        office_id=office_id,
        style=style,
        plan=plan_type,
        processing_time_ms=result.processing_time_ms,
    )

    # 6. Response olustur
    return StagingResponse(
        staged_images=[
            StagedImageItem(base64=staged_image_to_base64(img))
            for img in result.staged_images
        ],
        room_analysis=RoomAnalysisResponse(
            room_type=result.room_analysis.room_type,
            is_empty=result.room_analysis.is_empty,
            floor_type=result.room_analysis.floor_type,
            estimated_size=result.room_analysis.estimated_size,
            wall_color=result.room_analysis.wall_color,
            natural_light=result.room_analysis.natural_light,
            window_count=result.room_analysis.window_count,
            special_features=list(result.room_analysis.special_features),
        ),
        style=result.style,
        processing_time_ms=result.processing_time_ms,
    )


# ================================================================
# GET /staging-styles — Public endpoint
# ================================================================


@router.get(
    "/staging-styles",
    status_code=status.HTTP_200_OK,
    response_model=StyleListResponse,
    summary="Sahneleme tarzlarini listele",
    description="Kullanilabilir tum sahneleme tarzlarini dondurur. Public endpoint.",
)
async def list_staging_styles() -> StyleListResponse:
    """Tum tarzlarin listesini dondurur — kimlik dogrulama gerektirmez."""
    styles = get_available_styles()
    return StyleListResponse(
        styles=[
            StyleInfo(id=s["id"], name_tr=s["name_tr"], description=s["description"])
            for s in styles
        ],
        count=len(styles),
    )


# ================================================================
# POST /analyze-room — JWT zorunlu, sadece oda analizi
# ================================================================


@router.post(
    "/analyze-room",
    status_code=status.HTTP_200_OK,
    response_model=RoomAnalysisResponse,
    summary="Oda fotografini analiz et",
    description=(
        "Oda fotografini GPT-5-mini Vision ile analiz eder. "
        "Oda tipi, bosluk durumu, zemin, isik bilgisi dondurur. "
        "Sahneleme yapmaz, yalnizca analiz yapar."
    ),
)
async def analyze_room_endpoint(
    image: UploadFile,
    user: ActiveUser,
) -> RoomAnalysisResponse:
    """
    Oda analiz endpoint'i — sahneleme oncesi on-kontrol icin.

    Kota tuketmez, sadece Vision API kullanir.
    """
    image_bytes = await image.read()
    if not image_bytes:
        raise ValidationError(detail="Gorsel dosyasi bos.")

    analysis = await analyze_room(image_bytes)

    logger.info(
        "staging_analyze_endpoint",
        user_id=str(user.id),
        room_type=analysis.room_type,
        is_empty=analysis.is_empty,
    )

    return RoomAnalysisResponse(
        room_type=analysis.room_type,
        is_empty=analysis.is_empty,
        floor_type=analysis.floor_type,
        estimated_size=analysis.estimated_size,
        wall_color=analysis.wall_color,
        natural_light=analysis.natural_light,
        window_count=analysis.window_count,
        special_features=list(analysis.special_features),
    )
