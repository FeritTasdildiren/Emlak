"""
Emlak Teknoloji Platformu - Admin Outbox Monitor Router

Outbox worker saglik izleme admin endpoint'leri.

Prefix: /admin/outbox
Guvenlik: Tum endpoint'ler JWT gerektirir (ActiveUser + platform_admin rolu).
          PUBLIC_PATHS'e EKLENMEZ — TenantMiddleware JWT dogrulamasi zorunlu.

Endpoint'ler:
    GET    /admin/outbox/metrics              → Outbox metriklerini getir
    GET    /admin/outbox/stuck                → Stuck event'leri listele
    POST   /admin/outbox/stuck/{event_id}/release → Stuck event'i zorla serbest birak

Referans: TASK-040
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, Request

from src.core.exceptions import NotFoundError
from src.modules.auth.dependencies import require_role

logger = structlog.get_logger()

router = APIRouter(
    prefix="/admin/outbox",
    tags=["admin", "outbox-monitor"],
    # Tum endpoint'ler platform_admin rolu gerektirir
    dependencies=[Depends(require_role("platform_admin"))],
)


# ---------- GET /admin/outbox/metrics ----------


@router.get(
    "/metrics",
    summary="Outbox metriklerini getir",
    description="Outbox worker saglik metrikleri: lag, pending/stuck sayilari.",
)
async def get_outbox_metrics(request: Request) -> dict:
    """
    Outbox lag istatistiklerini dondurur.

    Icerdigi metrikler:
        - pending_count, processing_count, failed_count, dead_letter_count
        - stuck_count (5dk+ processing'de kalan)
        - lag istatistikleri (avg, max, p95)
        - oldest_pending_at (en eski bekleyen event)
    """
    monitor = request.app.state.outbox_monitor
    return await monitor.get_lag_stats()


# ---------- GET /admin/outbox/stuck ----------


@router.get(
    "/stuck",
    summary="Stuck event'leri listele",
    description="5 dakikadan uzun suredir processing durumunda olan event'ler.",
)
async def list_stuck_events(request: Request) -> dict:
    """
    Stuck durumundaki outbox event'lerini listeler.

    Stuck: processing durumunda 5dk'dan uzun suredir kalan event'ler.
    Bu event'ler muhtemelen worker crash veya timeout nedeniyle
    stuck kalmistir ve manuel mudahale gerektirebilir.
    """
    monitor = request.app.state.outbox_monitor
    stuck_events = await monitor.check_stuck_events()

    return {
        "stuck_count": len(stuck_events),
        "stuck_threshold_seconds": monitor._stuck_threshold,
        "events": [event.to_dict() for event in stuck_events],
    }


# ---------- POST /admin/outbox/stuck/{event_id}/release ----------


@router.post(
    "/stuck/{event_id}/release",
    summary="Stuck event'i zorla serbest birak",
    description="Stuck event'i pending'e dondurur — worker tekrar dener.",
)
async def release_stuck_event(
    event_id: uuid.UUID,
    request: Request,
) -> dict:
    """
    Stuck event'i zorla serbest birakir.

    Event'i silmez; status'u pending'e dondurur ve lock bilgisini temizler.
    Worker bir sonraki poll'da bu event'i tekrar alir ve isler.

    Sadece gercekten stuck olan event'ler serbest birakilabilir
    (processing durumunda VE 5dk+ locked_at).

    Args:
        event_id: Serbest birakilacak event UUID'si.

    Returns:
        Basari durumu ve mesaj.

    Raises:
        NotFoundError: Event bulunamadi veya stuck degil.
    """
    monitor = request.app.state.outbox_monitor
    released = await monitor.force_release_stuck(str(event_id))

    if not released:
        raise NotFoundError(
            resource="OutboxEvent (stuck)",
            resource_id=str(event_id),
        )

    logger.info(
        "admin_outbox_event_released",
        event_id=str(event_id),
        released_by=getattr(request.state, "user_id", None),
    )

    return {
        "released": True,
        "event_id": str(event_id),
        "message": "Event basariyla serbest birakildi. Worker tekrar deneyecek.",
    }
