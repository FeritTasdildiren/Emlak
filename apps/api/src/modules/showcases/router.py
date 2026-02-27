"""
Emlak Teknoloji Platformu - Showcases Router

Vitrin (Showcase) CRUD API endpoint'leri + Public erisim.

Prefix: /api/v1/showcases
Guvenlik:
    - CRUD endpoint'ler JWT gerektirir (ActiveUser dependency).
    - Public endpoint'ler (/public/{slug}) JWT gerektirmez.
    - Tenant izolasyonu: office_id otomatik olarak JWT'den alinir.

Endpoint'ler:
    POST   /showcases                    -> Yeni vitrin olustur (JWT)
    GET    /showcases                    -> Kendi vitrinlerini listele (JWT)
    GET    /showcases/{id}               -> Vitrin detay (JWT)
    PUT    /showcases/{id}               -> Vitrin guncelle (JWT)
    DELETE /showcases/{id}               -> Vitrin sil (JWT)
    GET    /showcases/public/{slug}      -> Public vitrin gorunumu (JWT gereksiz)
    POST   /showcases/public/{slug}/view -> Goruntulenme sayaci (JWT gereksiz)
    GET    /showcases/public/{slug}/whatsapp -> WhatsApp click-to-chat link (JWT gereksiz)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    import uuid
from fastapi import APIRouter, status

from src.dependencies import DBSession
from src.modules.auth.dependencies import ActiveUser
from src.modules.showcases.schemas import (
    PropertySummary,
    SharedShowcaseItem,
    SharedShowcaseListResponse,
    ShowcaseCreate,
    ShowcaseListItem,
    ShowcaseListResponse,
    ShowcasePublicResponse,
    ShowcaseResponse,
    ShowcaseUpdate,
    WhatsAppLinkResponse,
)
from src.modules.showcases.service import ShowcaseService

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/showcases",
    tags=["showcases"],
)


# ================================================================
# Helper: Entity -> Response donusturuculer
# ================================================================


def _to_response(showcase) -> ShowcaseResponse:
    """Showcase entity'sini response modeline donusturur."""
    return ShowcaseResponse(
        id=str(showcase.id),
        title=showcase.title,
        slug=showcase.slug,
        description=showcase.description,
        selected_properties=showcase.selected_properties or [],
        agent_phone=showcase.agent_phone,
        agent_email=showcase.agent_email,
        agent_whatsapp=showcase.agent_whatsapp,
        theme=showcase.theme,
        is_active=showcase.is_active,
        views_count=showcase.views_count or 0,
        created_at=showcase.created_at,
        updated_at=showcase.updated_at,
    )


def _to_list_item(showcase) -> ShowcaseListItem:
    """Showcase entity'sini liste gorunumune donusturur."""
    return ShowcaseListItem(
        id=str(showcase.id),
        title=showcase.title,
        slug=showcase.slug,
        is_active=showcase.is_active,
        views_count=showcase.views_count or 0,
        created_at=showcase.created_at,
    )


def _to_shared_item(showcase) -> SharedShowcaseItem:
    """Showcase entity'sini paylasim agi listesi gorunumune donusturur."""
    agent_name = "Bilinmiyor"
    if showcase.agent and hasattr(showcase.agent, "full_name"):
        agent_name = showcase.agent.full_name

    office_name = None
    if showcase.office and hasattr(showcase.office, "name"):
        office_name = showcase.office.name

    selected = showcase.selected_properties or []
    return SharedShowcaseItem(
        id=str(showcase.id),
        title=showcase.title,
        slug=showcase.slug,
        description=showcase.description,
        agent_name=agent_name,
        agent_phone=showcase.agent_phone,
        property_count=len(selected),
        views_count=showcase.views_count or 0,
        office_name=office_name,
        created_at=showcase.created_at,
    )


def _to_property_summary(prop) -> PropertySummary:
    """Property entity'sini vitrin icindeki ozet gorunumune donusturur."""
    # photo_urls: JSONB array veya None olabilir
    photo_urls = []
    if hasattr(prop, "photo_urls") and prop.photo_urls:
        photo_urls = prop.photo_urls if isinstance(prop.photo_urls, list) else []

    return PropertySummary(
        id=str(prop.id),
        title=prop.title if hasattr(prop, "title") else None,
        listing_type=prop.listing_type if hasattr(prop, "listing_type") else None,
        property_type=prop.property_type if hasattr(prop, "property_type") else None,
        price=float(prop.price) if hasattr(prop, "price") and prop.price else None,
        currency=prop.currency if hasattr(prop, "currency") else None,
        city=prop.city if hasattr(prop, "city") else None,
        district=prop.district if hasattr(prop, "district") else None,
        neighborhood=prop.neighborhood if hasattr(prop, "neighborhood") else None,
        net_sqm=float(prop.net_sqm) if hasattr(prop, "net_sqm") and prop.net_sqm else None,
        gross_sqm=float(prop.gross_sqm) if hasattr(prop, "gross_sqm") and prop.gross_sqm else None,
        room_count=prop.room_count if hasattr(prop, "room_count") else None,
        building_age=prop.building_age if hasattr(prop, "building_age") else None,
        floor_number=prop.floor_number if hasattr(prop, "floor_number") else None,
        total_floors=prop.total_floors if hasattr(prop, "total_floors") else None,
        photo_urls=photo_urls,
    )


# ================================================================
# PUBLIC Endpoint'ler (JWT gereksiz, tenant filtresi yok)
# ONEMLI: Bu endpoint'ler /showcases/{showcase_id} path'inden
# ONCE tanimlanmali, yoksa FastAPI "public" kelimesini UUID olarak
# parse etmeye calisir ve 422 doner.
# ================================================================


# ---------- GET /showcases/public/{slug} ----------


@router.get(
    "/public/{slug}",
    response_model=ShowcasePublicResponse,
    summary="Public vitrin gorunumu",
    description=(
        "Vitrin slug'i ile public gorunum dondurur. "
        "JWT gerektirmez. Ilanlarin detayli bilgilerini icerir."
    ),
)
async def get_public_showcase(
    slug: str,
    db: DBSession,
) -> ShowcasePublicResponse:
    """
    Public vitrin gorunumunu getirir.

    - JWT gerektirmez, herkes erisebilir
    - Sadece aktif vitrinler dondurulur
    - Ilan detaylari (fotograf, fiyat, konum vb.) dahil edilir
    """
    showcase = await ShowcaseService.get_by_slug(db=db, slug=slug)

    # Vitrine ait ilanlari getir
    properties = await ShowcaseService.get_showcase_properties(
        db=db,
        property_ids=showcase.selected_properties or [],
    )

    return ShowcasePublicResponse(
        slug=showcase.slug,
        title=showcase.title,
        description=showcase.description,
        agent_phone=showcase.agent_phone,
        agent_email=showcase.agent_email,
        agent_whatsapp=showcase.agent_whatsapp,
        agent_photo_url=showcase.agent_photo_url,
        theme=showcase.theme,
        properties=[_to_property_summary(p) for p in properties],
        views_count=showcase.views_count or 0,
    )


# ---------- POST /showcases/public/{slug}/view ----------


@router.post(
    "/public/{slug}/view",
    status_code=status.HTTP_200_OK,
    summary="Goruntulenme sayaci arttir",
    description="Vitrin goruntulenme sayacini 1 arttirir. JWT gerektirmez.",
)
async def increment_showcase_views(
    slug: str,
    db: DBSession,
) -> dict:
    """
    Vitrin goruntulenme sayacini arttirir.

    - JWT gerektirmez
    - Sadece aktif vitrinler icin calisir
    - Guncel goruntulenme sayisini dondurur
    """
    views_count = await ShowcaseService.increment_views(db=db, slug=slug)
    return {"views_count": views_count}


# ---------- GET /showcases/public/{slug}/whatsapp ----------


@router.get(
    "/public/{slug}/whatsapp",
    response_model=WhatsAppLinkResponse,
    summary="WhatsApp click-to-chat link",
    description=(
        "Vitrin slug'i ile WhatsApp click-to-chat linki dondurur. "
        "JWT gerektirmez. Danisman telefonu vitrin kaydindaki agent_phone alanindadir."
    ),
)
async def get_whatsapp_link(
    slug: str,
    db: DBSession,
) -> WhatsAppLinkResponse:
    """
    WhatsApp click-to-chat linkini dondurur.

    - JWT gerektirmez, herkes erisebilir
    - Sadece aktif vitrinler icin calisir
    - agent_phone bos ise 404 doner
    """
    from fastapi import HTTPException

    showcase = await ShowcaseService.get_by_slug(db=db, slug=slug)

    phone = showcase.agent_whatsapp or showcase.agent_phone
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bu vitrin icin WhatsApp numarasi tanimlanmamis.",
        )

    try:
        whatsapp_url = ShowcaseService.generate_whatsapp_link(
            phone=phone,
            showcase_title=showcase.title,
            slug=showcase.slug,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Gecersiz telefon numarasi.",
        ) from None

    logger.info(
        "whatsapp_link_generated",
        slug=slug,
    )

    return WhatsAppLinkResponse(whatsapp_url=whatsapp_url)


# ================================================================
# Authenticated Endpoint'ler (JWT zorunlu)
# ================================================================


# ---------- GET /showcases/shared ----------
# ONEMLI: Bu endpoint /{showcase_id} path'inden ONCE tanimlanmali,
# yoksa FastAPI "shared" kelimesini UUID olarak parse etmeye calisir.


@router.get(
    "/shared",
    response_model=SharedShowcaseListResponse,
    summary="Paylasim agindaki vitrinleri listele",
    description=(
        "Diger ofislerin paylasima actigi aktif vitrinleri listeler. "
        "Kendi ofisinizin vitrinleri haric tutulur."
    ),
)
async def list_shared_showcases(
    db: DBSession,
    current_user: ActiveUser,
    skip: int = 0,
    limit: int = 20,
) -> SharedShowcaseListResponse:
    """
    Paylasim agindaki vitrinleri listeler.

    - JWT zorunlu (giris yapmis kullanici)
    - Kendi ofisinin vitrinleri haric tutulur
    - Sadece aktif ve en az 1 ilan secili vitrinler doner
    - En yeniden en eskiye siralanir
    - Pagination: skip/limit (default 0/20)
    """
    showcases, total = await ShowcaseService.list_shared(
        db=db,
        exclude_office_id=current_user.office_id,
        skip=skip,
        limit=limit,
    )
    return SharedShowcaseListResponse(
        items=[_to_shared_item(s) for s in showcases],
        total=total,
    )


# ---------- POST /showcases ----------


@router.post(
    "",
    response_model=ShowcaseResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni vitrin olustur",
    description="Authenticated kullanicinin ofisine yeni vitrin ekler.",
)
async def create_showcase(
    body: ShowcaseCreate,
    db: DBSession,
    current_user: ActiveUser,
) -> ShowcaseResponse:
    """
    Yeni vitrin olusturur.

    - office_id ve agent_id JWT'den otomatik alinir
    - Slug basliktan otomatik olusturulur (Turkce karakterler temizlenir)
    - selected_properties: mevcut ilanlarin UUID listesi
    """
    showcase = await ShowcaseService.create(
        db=db,
        office_id=current_user.office_id,
        agent_id=current_user.id,
        data=body.model_dump(),
    )
    return _to_response(showcase)


# ---------- GET /showcases ----------


@router.get(
    "",
    response_model=ShowcaseListResponse,
    summary="Vitrinlerimi listele",
    description="Authenticated kullanicinin kendi vitrinlerini listeler.",
)
async def list_showcases(
    db: DBSession,
    current_user: ActiveUser,
) -> ShowcaseListResponse:
    """
    Kullanicinin kendi vitrinlerini listeler.

    - Sadece kendi ofisinin ve kendi olusturdugu vitrinler doner
    - En yeniden en eskiye siralanir
    """
    showcases, total = await ShowcaseService.list_by_agent(
        db=db,
        office_id=current_user.office_id,
        agent_id=current_user.id,
    )
    return ShowcaseListResponse(
        items=[_to_list_item(s) for s in showcases],
        total=total,
    )


# ---------- GET /showcases/{showcase_id} ----------


@router.get(
    "/{showcase_id}",
    response_model=ShowcaseResponse,
    summary="Vitrin detay",
    description="Belirtilen vitrinin detaylarini dondurur.",
)
async def get_showcase(
    showcase_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> ShowcaseResponse:
    """
    Vitrin detayini getirir.

    - Sadece kendi ofisinin vitrinleri gorulebilir (tenant isolation)
    - Vitrin bulunamazsa 404
    """
    showcase = await ShowcaseService.get_by_id(
        db=db,
        showcase_id=showcase_id,
        office_id=current_user.office_id,
    )
    return _to_response(showcase)


# ---------- PUT /showcases/{showcase_id} ----------


@router.put(
    "/{showcase_id}",
    response_model=ShowcaseResponse,
    summary="Vitrin guncelle",
    description="Belirtilen vitrinin bilgilerini gunceller. Sadece gonderilen alanlar degisir.",
)
async def update_showcase(
    showcase_id: uuid.UUID,
    body: ShowcaseUpdate,
    db: DBSession,
    current_user: ActiveUser,
) -> ShowcaseResponse:
    """
    Vitrini gunceller.

    - Partial update: sadece gonderilen alanlar guncellenir
    - Baslik degisirse slug otomatik yeniden olusturulur
    - Vitrin bulunamazsa 404
    """
    showcase = await ShowcaseService.update(
        db=db,
        showcase_id=showcase_id,
        office_id=current_user.office_id,
        data=body.model_dump(exclude_unset=True),
    )
    return _to_response(showcase)


# ---------- DELETE /showcases/{showcase_id} ----------


@router.delete(
    "/{showcase_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Vitrin sil",
    description="Belirtilen vitrini kalici olarak siler.",
)
async def delete_showcase(
    showcase_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> None:
    """
    Vitrini siler (hard delete).

    - Vitrin bulunamazsa 404
    """
    await ShowcaseService.delete(
        db=db,
        showcase_id=showcase_id,
        office_id=current_user.office_id,
    )
