"""
Emlak Teknoloji Platformu - Properties Router

Ilan CRUD + paylasim ayarlari endpoint'leri.

Prefix: /api/v1/properties
Guvenlik: Tum endpoint'ler JWT gerektirir (ActiveUser dependency).
Tenant izolasyonu: office_id otomatik olarak JWT'den alinir.

Endpoint'ler:
    GET   /properties/{id}         -> Ilan detay (JWT)
    PATCH /properties/{id}/sharing -> Paylasim ayarlarini guncelle (JWT)
"""

from __future__ import annotations

import uuid  # noqa: TC003 — FastAPI path param runtime resolution icin gerekli
from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Request
from geoalchemy2 import Geometry
from sqlalchemy import func, select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.dependencies import DBSession
from src.models.property import Property
from src.modules.audit.audit_service import AuditService
from src.modules.auth.dependencies import ActiveUser
from src.modules.properties.schemas import PropertyDetailResponse
from src.modules.showcases.schemas import PropertySharingResponse, PropertySharingUpdate

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/properties",
    tags=["properties"],
)


# ---------- Helpers ----------


async def _get_property(
    db: AsyncSession,
    property_id: uuid.UUID,
    office_id: uuid.UUID,
) -> Property:
    """Ilani ID ile getirir, tenant izolasyonlu."""
    result = await db.execute(
        select(Property).where(
            Property.id == property_id,
            Property.office_id == office_id,
        )
    )
    prop = result.scalar_one_or_none()
    if prop is None:
        raise NotFoundError(resource="Ilan", resource_id=str(property_id))
    return prop


# ---------- GET /properties/{property_id} ----------


@router.get(
    "/{property_id}",
    response_model=PropertyDetailResponse,
    summary="Ilan detay",
    description="Belirtilen ilanin tum detaylarini dondurur. JWT zorunlu, tenant izolasyonlu.",
)
async def get_property_detail(
    property_id: uuid.UUID,
    db: DBSession,
    current_user: ActiveUser,
) -> PropertyDetailResponse:
    """
    Ilan detayini getirir.

    - Sadece kendi ofisinin ilanlari gorulebilir (tenant isolation)
    - Ilan bulunamazsa 404
    - Koordinatlar PostGIS GEOGRAPHY'den cikarilir
    """
    # Property entity + koordinatlari tek sorguda getir
    stmt = (
        select(
            Property,
            func.ST_Y(
                Property.location.cast(Geometry)
            ).label("lat"),
            func.ST_X(
                Property.location.cast(Geometry)
            ).label("lon"),
        )
        .where(
            Property.id == property_id,
            Property.office_id == current_user.office_id,
        )
    )
    result = await db.execute(stmt)
    row = result.one_or_none()

    if row is None:
        raise NotFoundError(resource="Ilan", resource_id=str(property_id))

    prop = row[0]
    lat = row[1]
    lon = row[2]

    return PropertyDetailResponse(
        id=str(prop.id),
        title=prop.title,
        description=prop.description,
        property_type=prop.property_type,
        listing_type=prop.listing_type,
        price=float(prop.price),
        currency=prop.currency,
        rooms=prop.rooms,
        gross_area=float(prop.gross_area) if prop.gross_area is not None else None,
        net_area=float(prop.net_area) if prop.net_area is not None else None,
        floor_number=prop.floor_number,
        total_floors=prop.total_floors,
        building_age=prop.building_age,
        heating_type=prop.heating_type,
        bathroom_count=prop.bathroom_count,
        furniture_status=prop.furniture_status,
        building_type=prop.building_type,
        facade=prop.facade,
        city=prop.city,
        district=prop.district,
        neighborhood=prop.neighborhood,
        address=prop.address,
        latitude=float(lat) if lat is not None else None,
        longitude=float(lon) if lon is not None else None,
        photos=prop.photos or [],
        status=prop.status,
        created_at=prop.created_at,
        updated_at=prop.updated_at,
    )


# ---------- PATCH /properties/{property_id}/sharing ----------


@router.patch(
    "/{property_id}/sharing",
    response_model=PropertySharingResponse,
    summary="Ilan paylasim ayarlarini guncelle",
    description=(
        "Ilanin ofisler arasi paylasim durumunu ve gorunurlugunu gunceller. "
        "is_shared: true yapildiginda ilan diger ofislerce gorulebilir hale gelir."
    ),
)
async def update_property_sharing(
    request: Request,
    property_id: uuid.UUID,
    body: PropertySharingUpdate,
    db: DBSession,
    current_user: ActiveUser,
) -> PropertySharingResponse:
    """
    Ilan paylasim ayarlarini gunceller.

    - is_shared: Ofisler arasi paylasima ac/kapat
    - share_visibility: private | shared | public
    - Ilan bulunamazsa 404
    """
    prop = await _get_property(
        db=db,
        property_id=property_id,
        office_id=current_user.office_id,
    )

    prop.is_shared = body.is_shared
    prop.share_visibility = body.share_visibility

    await db.flush()

    logger.info(
        "property_sharing_updated",
        property_id=str(property_id),
        office_id=str(current_user.office_id),
        is_shared=body.is_shared,
        share_visibility=body.share_visibility,
    )

    # KVKK Audit: Ilan guncelleme kaydi
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        office_id=current_user.office_id,
        action="UPDATE",
        entity_type="Property",
        entity_id=str(property_id),
        new_value={
            "is_shared": body.is_shared,
            "share_visibility": body.share_visibility,
        },
        request=request,
    )

    return PropertySharingResponse(
        id=str(prop.id),
        is_shared=prop.is_shared,
        share_visibility=prop.share_visibility,
    )
