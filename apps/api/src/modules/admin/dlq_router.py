"""
Emlak Teknoloji Platformu - Admin DLQ Router

Dead Letter Queue yonetim endpoint'leri.

Prefix: /admin/dlq
Guvenlik: Tum endpoint'ler JWT gerektirir (ActiveUser + platform_admin rolu).
          PUBLIC_PATHS'e EKLENMEZ — TenantMiddleware JWT dogrulamasi zorunlu.

Endpoint'ler:
    GET    /admin/dlq              -> Dead letter event'leri listele
    GET    /admin/dlq/count        -> Dead letter sayisini getir
    POST   /admin/dlq/{id}/retry   -> Tek event'i retry'a gonder
    POST   /admin/dlq/retry-all    -> Tum event'leri retry'a gonder
    DELETE /admin/dlq/purge        -> Eski event'leri temizle

Referans: TASK-041
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Depends, Query, Request

from src.core.exceptions import NotFoundError
from src.modules.admin.schemas import (
    DeadLetterCountResponse,
    DeadLetterListResponse,
    DeadLetterResponse,
    PurgeResponse,
    RetryAllResponse,
    RetryResponse,
)
from src.modules.auth.dependencies import require_role

logger = structlog.get_logger()

router = APIRouter(
    prefix="/admin/dlq",
    tags=["admin", "dlq"],
    # Tum endpoint'ler platform_admin rolu gerektirir (TASK-040 pattern)
    dependencies=[Depends(require_role("platform_admin"))],
)


# ---------- GET /admin/dlq ----------


@router.get(
    "",
    response_model=DeadLetterListResponse,
    summary="Dead letter event'leri listele",
    description="DLQ'daki event'leri sayfalanmis olarak listeler.",
)
async def list_dead_letters(
    request: Request,
    limit: int = Query(default=50, ge=1, le=100, description="Sayfa basina kayit"),
    offset: int = Query(default=0, ge=0, description="Baslangic noktasi"),
    event_type: str | None = Query(
        default=None,
        description="Event tipi filtresi (or: payment.completed)",
    ),
) -> DeadLetterListResponse:
    """
    Dead letter durumundaki event'leri listeler.

    Sayfalama: limit + offset ile.
    Filtreleme: event_type ile opsiyonel.
    Siralama: created_at DESC (en yeni once).
    """
    dlq_service = request.app.state.dlq_service
    items = await dlq_service.list_dead_letters(
        limit=limit,
        offset=offset,
        event_type=event_type,
    )

    # Toplam sayi (pagination icin)
    count_data = await dlq_service.count_dead_letters(event_type=event_type)

    return DeadLetterListResponse(
        items=[DeadLetterResponse(**item) for item in items],
        total=count_data["total"],
        limit=limit,
        offset=offset,
    )


# ---------- GET /admin/dlq/count ----------


@router.get(
    "/count",
    response_model=DeadLetterCountResponse,
    summary="Dead letter sayisini getir",
    description="DLQ'daki event sayisini event tipi bazinda dondurur.",
)
async def count_dead_letters(
    request: Request,
    event_type: str | None = Query(
        default=None,
        description="Event tipi filtresi",
    ),
) -> DeadLetterCountResponse:
    """
    Dead letter event sayisini dondurur.

    Toplam sayi + event tipi bazinda dagilim.
    """
    dlq_service = request.app.state.dlq_service
    count_data = await dlq_service.count_dead_letters(event_type=event_type)

    return DeadLetterCountResponse(
        total=count_data["total"],
        by_event_type=count_data["by_event_type"],
    )


# ---------- POST /admin/dlq/{id}/retry ----------


@router.post(
    "/{event_id}/retry",
    response_model=RetryResponse,
    summary="Tek event'i retry'a gonder",
    description=(
        "Dead letter event'i pending durumuna dondurur. "
        "ONEMLI: retry_count SIFIRLANMAZ — toplam deneme sayisi korunur."
    ),
)
async def retry_single(
    event_id: uuid.UUID,
    request: Request,
) -> RetryResponse:
    """
    Tek bir dead letter event'i retry'a geri gonderir.

    retry_count SIFIRLANMAZ:
        Toplam deneme sayisi korunur. Event pending'e doner
        ve worker bir sonraki poll'da alir. Eger max_retries
        asilmissa, policy buna gore tekrar DLQ'ya gonderir.
    """
    dlq_service = request.app.state.dlq_service
    success = await dlq_service.retry_single(str(event_id))

    if not success:
        raise NotFoundError(
            resource="DeadLetterEvent",
            resource_id=str(event_id),
        )

    logger.info(
        "admin_dlq_retry_single",
        event_id=str(event_id),
        retried_by=getattr(request.state, "user_id", None),
    )

    return RetryResponse(
        success=True,
        event_id=str(event_id),
        message="Event basariyla pending durumuna donduruldu. Worker tekrar deneyecek.",
    )


# ---------- POST /admin/dlq/retry-all ----------


@router.post(
    "/retry-all",
    response_model=RetryAllResponse,
    summary="Tum event'leri retry'a gonder",
    description=(
        "Tum dead letter event'leri pending durumuna dondurur. "
        "ONEMLI: retry_count SIFIRLANMAZ — toplam deneme sayisi korunur."
    ),
)
async def retry_all(
    request: Request,
    event_type: str | None = Query(
        default=None,
        description="Sadece belirli event tipini retry'a gonder",
    ),
) -> RetryAllResponse:
    """
    Tum dead letter event'leri retry'a geri gonderir.

    retry_count SIFIRLANMAZ:
        Tum event'ler pending'e doner. Her birinin mevcut
        retry_count'u korunur.

    Filtreleme: event_type ile opsiyonel.
    """
    dlq_service = request.app.state.dlq_service
    retried_count = await dlq_service.retry_all(event_type=event_type)

    logger.info(
        "admin_dlq_retry_all",
        retried_count=retried_count,
        event_type_filter=event_type,
        retried_by=getattr(request.state, "user_id", None),
    )

    return RetryAllResponse(
        success=True,
        retried_count=retried_count,
        message=f"{retried_count} event basariyla pending durumuna donduruldu.",
    )


# ---------- DELETE /admin/dlq/purge ----------


@router.delete(
    "/purge",
    response_model=PurgeResponse,
    summary="Eski dead letter event'leri temizle",
    description=(
        "Belirtilen saatten eski dead letter event'leri kalici olarak siler. "
        "GUVENLIK: older_than_hours parametresi yeni event'lerin silinmesini engeller."
    ),
)
async def purge_dead_letters(
    request: Request,
    older_than_hours: int = Query(
        default=168,
        ge=1,
        description="Bu saatten eski event'ler silinir (varsayilan: 168 = 7 gun)",
    ),
    event_type: str | None = Query(
        default=None,
        description="Sadece belirli event tipini temizle",
    ),
) -> PurgeResponse:
    """
    Eski dead letter event'leri kalici olarak siler.

    Guvenlik Onlemleri:
        - older_than_hours minimum 1 saat (yeni event'ler korunur)
        - Varsayilan 168 saat (7 gun) — sadece 1 haftadan eski event'ler
        - event_type filtresi ile hedefli temizlik
    """
    dlq_service = request.app.state.dlq_service
    purged_count = await dlq_service.purge(
        older_than_hours=older_than_hours,
        event_type=event_type,
    )

    logger.info(
        "admin_dlq_purge",
        purged_count=purged_count,
        older_than_hours=older_than_hours,
        event_type_filter=event_type,
        purged_by=getattr(request.state, "user_id", None),
    )

    return PurgeResponse(
        success=True,
        purged_count=purged_count,
        older_than_hours=older_than_hours,
        message=f"{purged_count} event kalici olarak silindi ({older_than_hours} saatten eski).",
    )
