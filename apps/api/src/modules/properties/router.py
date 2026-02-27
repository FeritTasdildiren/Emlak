"""
Emlak Teknoloji Platformu - Properties Router

Ilan CRUD + paylasim ayarlari endpoint'leri.

Prefix: /api/v1/properties
Guvenlik: Tum endpoint'ler JWT gerektirir (ActiveUser dependency).
Tenant izolasyonu: office_id otomatik olarak JWT'den alinir.

Endpoint'ler:
    PATCH /properties/{id}/sharing -> Paylasim ayarlarini guncelle (JWT)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Request
from sqlalchemy import select

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError
from src.dependencies import DBSession
from src.models.property import Property
from src.modules.audit.audit_service import AuditService
from src.modules.auth.dependencies import ActiveUser
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
