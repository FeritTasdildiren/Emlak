"""
Emlak Teknoloji Platformu - Portal Export Router

Ilan metni ciktisini emlak portali formatina donusturup export eden endpoint'ler.

Prefix: /api/v1/listings
Guvenlik: POST /export JWT gerektirir (ActiveUser).
          GET /portals public endpoint'tir.

Referans: TASK-120 (S8.8 + S8.16)
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, status

from src.listings.portal_export_schemas import (
    PortalExportRequest,
    PortalExportResponse,
    PortalExportResult,
    PortalInfo,
    PortalListResponse,
)
from src.listings.portal_export_service import (
    export_to_multiple,
    format_for_portal,
    get_portal_info,
)
from src.modules.auth.dependencies import ActiveUser  # noqa: TC001 — FastAPI runtime

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/listings",
    tags=["portal-export"],
)


# ================================================================
# POST /export — JWT zorunlu
# ================================================================


@router.post(
    "/export",
    status_code=status.HTTP_200_OK,
    response_model=PortalExportResponse,
    summary="Ilan metnini portal formatina donustur",
    description=(
        "Ilan metni uretim ciktisini (baslik, aciklama, one cikan ozellikler) "
        "secilen emlak portali formatina cevirir. 'both' secilirse hem sahibinden "
        "hem hepsiemlak formati doner."
    ),
)
async def export_to_portal(
    body: PortalExportRequest,
    user: ActiveUser,
) -> PortalExportResponse:
    """
    Portal export endpoint'i.

    Akis:
        1. JWT dogrulama
        2. portal='both' ise her iki portal, degilse tek portal icin formatlama
        3. PortalExportResponse dondur
    """
    text_result = {
        "title": body.title,
        "description": body.description,
        "highlights": body.highlights,
    }

    # Portal secimi: 'both' ise her ikisi, degilse tek portal
    if body.portal == "both":
        portals = ["sahibinden", "hepsiemlak"]
        results = export_to_multiple(text_result, portals)
    else:
        result = format_for_portal(text_result, body.portal)
        results = [result]

    logger.info(
        "portal_export_endpoint_success",
        user_id=str(user.id),
        office_id=str(user.office_id),
        portal=body.portal,
        export_count=len(results),
    )

    return PortalExportResponse(
        exports=[
            PortalExportResult(
                portal=r["portal"],
                formatted_title=r["formatted_title"],
                formatted_description=r["formatted_description"],
                character_counts=r["character_counts"],
                warnings=r["warnings"],
            )
            for r in results
        ],
    )


# ================================================================
# GET /portals — Public endpoint
# ================================================================


@router.get(
    "/portals",
    status_code=status.HTTP_200_OK,
    response_model=PortalListResponse,
    summary="Desteklenen portallari listele",
    description="Desteklenen tum emlak portallarinin format bilgilerini dondurur. Public endpoint.",
)
async def list_portals() -> PortalListResponse:
    """Tum portal bilgilerini dondurur — kimlik dogrulama gerektirmez."""
    portals = get_portal_info()
    return PortalListResponse(
        portals=[
            PortalInfo(
                id=p["id"],
                name=p["name"],
                max_title_length=p["max_title_length"],
                max_description_length=p["max_description_length"],
                emoji_allowed=p["emoji_allowed"],
                required_fields=p["required_fields"],
                notes=p["notes"],
            )
            for p in portals
        ],
        count=len(portals),
    )
