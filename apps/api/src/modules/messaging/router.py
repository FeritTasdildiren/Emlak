"""
Emlak Teknoloji Platformu - Messaging Capabilities Router

Kanal yetenek sorgulama API endpoint'leri (ADR-0007).

Prefix: /api/v1/messaging
Guvenlik: PUBLIC (ileride admin rolune sinirlanabilir)

Endpoint'ler:
    GET /capabilities             — Tum kanal yeteneklerini listele
    GET /capabilities/{channel}   — Belirli kanal yetenegini dondur
    GET /capabilities/search      — Belirli yeteneğe sahip kanallari bul

Kullanim:
    # Tum kanallar
    GET /api/v1/messaging/capabilities
    → {"channels": {"telegram": {...}, "whatsapp": {...}}, "total": 2}

    # Tek kanal
    GET /api/v1/messaging/capabilities/telegram
    → {"channel_name": "telegram", "supports_read": false, ...}

    # Yetenek bazli filtreleme
    GET /api/v1/messaging/capabilities/search?capability=read
    → {"capability": "read", "channels": ["whatsapp"], "total": 1}

Referans: ADR-0007, TASK-047
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, HTTPException, Query, Request, status

if TYPE_CHECKING:
    from src.modules.messaging.registry import ChannelRegistry

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/messaging",
    tags=["messaging-capabilities"],
)


# ================================================================
# Helper — ChannelRegistry DI
# ================================================================


def _get_registry(request: Request) -> ChannelRegistry:
    """
    app.state uzerinden ChannelRegistry instance'ina erisir.

    Raises:
        RuntimeError: ChannelRegistry app.state'te bulunamadi
            (lifespan'de yapilandirilmamis).
    """
    registry: ChannelRegistry | None = getattr(
        request.app.state, "channel_registry", None
    )
    if registry is None:
        raise RuntimeError(
            "ChannelRegistry app.state'te bulunamadi. "
            "Lifespan yapilandirmasini kontrol edin."
        )
    return registry


# ================================================================
# GET /capabilities — Tum kanal yetenekleri
# ================================================================


@router.get(
    "/capabilities",
    summary="Tum kanal yeteneklerini listele",
    description=(
        "Kayitli tum mesajlasma kanallarinin yetenek haritasini dondurur. "
        "UI bu bilgiyle dinamik ozellik gosterimi yapabilir. "
        "Admin dashboard ve kanal karsilastirma icin kullanilir."
    ),
)
async def list_capabilities(request: Request) -> dict:
    """
    Tum kayitli kanallarin yeteneklerini listeler.

    Response:
        {
            "channels": {
                "telegram": { ...capability fields... },
                "whatsapp": { ...capability fields... }
            },
            "total": 2
        }
    """
    registry = _get_registry(request)

    all_caps = registry.get_all_capabilities()

    logger.info(
        "capabilities_listed",
        channel_count=len(all_caps),
    )

    return {
        "channels": {
            name: caps.to_dict()
            for name, caps in all_caps.items()
        },
        "total": len(all_caps),
    }


# ================================================================
# GET /capabilities/search — Yetenek bazli kanal arama
# ================================================================


@router.get(
    "/capabilities/search",
    summary="Yeteneğe gore kanal ara",
    description=(
        "Belirli bir yetenegi destekleyen kanallari listeler. "
        "Ornegin: ?capability=read → read receipt destekleyen kanallar."
    ),
)
async def search_channels_by_capability(
    request: Request,
    capability: str = Query(
        ...,
        description=(
            "Aranacak yetenek adi ('supports_' prefix'i olmadan). "
            "Ornekler: read, inline_buttons, templates, voice"
        ),
        min_length=1,
        max_length=50,
    ),
) -> dict:
    """
    Belirli bir yetenegi destekleyen kanallari bulur.

    Response:
        {
            "capability": "read",
            "channels": ["whatsapp"],
            "total": 1
        }
    """
    registry = _get_registry(request)

    matching_channels = registry.get_channels_supporting(capability)

    logger.info(
        "capability_search",
        capability=capability,
        matching_count=len(matching_channels),
    )

    return {
        "capability": capability,
        "channels": matching_channels,
        "total": len(matching_channels),
    }


# ================================================================
# GET /capabilities/{channel} — Tek kanal yeteneği
# ================================================================


@router.get(
    "/capabilities/{channel}",
    summary="Belirli kanal yetenegini dondur",
    description=(
        "Belirtilen kanalin detayli yetenek haritasini dondurur. "
        "Kanal bulunamazsa 404 hatasi doner."
    ),
)
async def get_channel_capability(
    request: Request,
    channel: str,
) -> dict:
    """
    Belirtilen kanalin yeteneklerini dondurur.

    Args:
        channel: Kanal adi (path parametresi). Ornek: "telegram", "whatsapp"

    Response:
        { "channel_name": "telegram", "supports_read": false, ... }

    Raises:
        404: Kanal registry'de kayitli degil.
    """
    registry = _get_registry(request)

    try:
        caps = registry.get_capabilities(channel)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{channel}' kanali kayitli degil. "
            f"Mevcut kanallar: {registry.list_channels()}",
        )

    logger.info(
        "capability_queried",
        channel=channel,
    )

    return caps.to_dict()
