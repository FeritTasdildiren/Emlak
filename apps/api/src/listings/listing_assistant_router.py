"""
Emlak Teknoloji Platformu - Listing Assistant Router

Yapay zeka destekli ilan metni uretim endpoint'leri.

Prefix: /api/v1/listings
Guvenlik: generate-text ve regenerate-text JWT gerektirir (ActiveUser).
           tones public endpoint'tir.

Kota: POST /generate-text plan bazli aylik ilan kotasi uygular.
      POST /regenerate-text kota tuketmez (ton degisikligi).

Referans: TASK-118 (S8.2 + S8.3)
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, status
from sqlalchemy import select

from src.core.exceptions import QuotaExceededError, ValidationError
from src.dependencies import DBSession  # noqa: TC001 — FastAPI resolves at runtime
from src.listings.listing_assistant_schemas import (
    ListingTextRequest,
    ListingTextResponse,
    RegenerateRequest,
    ToneInfo,
    ToneListResponse,
)
from src.listings.listing_assistant_service import (
    generate_listing_text,
    get_available_tones,
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
    tags=["listing-assistant"],
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
# POST /generate-text — JWT zorunlu, JSON body
# ================================================================


@router.post(
    "/generate-text",
    status_code=status.HTTP_200_OK,
    response_model=ListingTextResponse,
    summary="Ilan metni uret",
    description=(
        "Verilen mulk bilgileri ve secilen tona gore yapay zeka destekli "
        "ilan metni, baslik, one cikan ozellikler ve SEO anahtar kelimeleri uretir. "
        "Plan bazli kota kontrolu uygulanir."
    ),
)
async def generate_text_endpoint(
    body: ListingTextRequest,
    user: ActiveUser,
    db: DBSession,
) -> ListingTextResponse:
    """
    Ilan metni uretim endpoint'i.

    Akis:
        1. JWT'den tenant_id + plan_type al
        2. Kota kontrolu (QuotaType.LISTING)
        3. listing_assistant_service.generate_listing_text() cagir
        4. Kota sayacini artir
        5. ListingTextResponse dondur
    """
    office_id = str(user.office_id)

    # 1. Plan tipini al
    plan_type = await _get_plan_type(db, office_id)

    # 2. Kota kontrolu
    is_allowed, used, limit = await check_quota(
        db,
        user.office_id,
        plan_type,
        QuotaType.LISTING,
    )

    if not is_allowed:
        has_credit = await check_credit(
            db,
            user.office_id,
            plan_type,
            QuotaType.LISTING,
        )
        if not has_credit:
            raise QuotaExceededError(
                limit=limit,
                used=used,
                plan=plan_type,
                detail="Aylik ilan metni uretim kotaniz doldu.",
            )
        # Kredi kullan
        await use_credit(db, user.office_id, plan_type, QuotaType.LISTING)

    # 3. Ilan metni uret
    try:
        result = await generate_listing_text(body)
    except ValueError as exc:
        raise ValidationError(detail=str(exc)) from exc

    # 4. Kota sayacini artir (kredi ile odenmemisse)
    if is_allowed:
        await increment_quota(db, user.office_id, plan_type, QuotaType.LISTING)

    logger.info(
        "listing_text_endpoint_success",
        user_id=str(user.id),
        office_id=office_id,
        tone=body.tone,
        plan=plan_type,
        token_usage=result["token_usage"],
    )

    # 5. Response olustur
    return ListingTextResponse(
        title=result["title"],
        description=result["description"],
        highlights=result["highlights"],
        seo_keywords=result["seo_keywords"],
        tone_used=result["tone_used"],
        token_usage=result["token_usage"],
    )


# ================================================================
# GET /tones — Public endpoint
# ================================================================


@router.get(
    "/tones",
    status_code=status.HTTP_200_OK,
    response_model=ToneListResponse,
    summary="Ilan tonu seceneklerini listele",
    description="Kullanilabilir tum ilan tonu seceneklerini dondurur. Public endpoint.",
)
async def list_tones() -> ToneListResponse:
    """Tum ton seceneklerinin listesini dondurur — kimlik dogrulama gerektirmez."""
    tones = get_available_tones()
    return ToneListResponse(
        tones=[
            ToneInfo(
                id=t["id"],
                name_tr=t["name_tr"],
                description=t["description"],
                example_phrase=t["example_phrase"],
            )
            for t in tones
        ],
        count=len(tones),
    )


# ================================================================
# POST /regenerate-text — JWT zorunlu, kota tuketmez
# ================================================================


@router.post(
    "/regenerate-text",
    status_code=status.HTTP_200_OK,
    response_model=ListingTextResponse,
    summary="Farkli tonla ilan metni yeniden uret",
    description=(
        "Ayni mulk bilgilerini farkli bir tonla yeniden uretir. "
        "Bu islem kota tuketmez — kullanici farkli tonlari denemek icin kullanir."
    ),
)
async def regenerate_text_endpoint(
    body: RegenerateRequest,
    user: ActiveUser,
    db: DBSession,
) -> ListingTextResponse:
    """
    Yeniden uretim endpoint'i — farkli tonla, kota tuketmez.

    Akis:
        1. JWT dogrulama (kota kontrolu YOK)
        2. listing_assistant_service.generate_listing_text() cagir
        3. ListingTextResponse dondur
    """
    try:
        result = await generate_listing_text(body)
    except ValueError as exc:
        raise ValidationError(detail=str(exc)) from exc

    logger.info(
        "listing_text_regenerate_success",
        user_id=str(user.id),
        office_id=str(user.office_id),
        tone=body.tone,
        token_usage=result["token_usage"],
    )

    return ListingTextResponse(
        title=result["title"],
        description=result["description"],
        highlights=result["highlights"],
        seo_keywords=result["seo_keywords"],
        tone_used=result["tone_used"],
        token_usage=result["token_usage"],
    )
