"""
Emlak Teknoloji Platformu - Payments Webhook Router

iyzico odeme bildirimi (webhook) endpoint'i.

Prefix: /webhooks/payments
Guvenlik: HMAC-SHA256 imza dogrulamasi (JWT gerektirmez, PUBLIC_PATHS'te)

Tasarim kararlari:
    - Webhook HER ZAMAN 200 dondurur (gecerli imza sonrasi).
      Boylece iyzico gereksiz retry yapmaz; hata varsa loglayip internal olarak cozemeliyiz.
    - Inbox pattern ile idempotency: ayni event_id tekrar gelirse 200 OK + skip.
    - Imza uyusmazligi → 403 Forbidden (tek istisna).
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy import select

from src.config import settings
from src.database import async_session_factory
from src.models.payment import Payment
from src.models.subscription import Subscription
from src.modules.payments.webhook import signature_error_response, verify_webhook_signature
from src.services.inbox_service import InboxService

logger = structlog.get_logger()

router = APIRouter(
    prefix="/webhooks/payments",
    tags=["webhooks"],
)

# Singleton inbox service
_inbox_service = InboxService()

# --- iyzico event type → Payment status mapping ---
_IYZICO_STATUS_MAP: dict[str, str] = {
    "success": "completed",
    "failure": "failed",
    "refund": "refunded",
}


@router.post(
    "/iyzico",
    status_code=status.HTTP_200_OK,
    summary="iyzico webhook callback",
    description=(
        "iyzico odeme saglayicisinin gonderdigi webhook bildirimi. "
        "HMAC-SHA256 imza dogrulamasi uygulanir."
    ),
)
async def iyzico_webhook(request: Request) -> JSONResponse:
    """
    iyzico payment webhook handler.

    Akis:
        1. HMAC-SHA256 imza dogrula → basarisiz ise 403
        2. Payload parse et
        3. InboxService.receive_event() ile dedup kontrol
        4. Duplicate ise → 200 OK (skip)
        5. Yeni event ise → Payment status guncelle + Subscription guncelle
        6. Her durumda 200 dondur (retry onleme)
    """
    request_id = getattr(request.state, "request_id", None)

    # ---- 1. Signature verification ----
    is_valid, raw_body = await verify_webhook_signature(
        request, settings.IYZICO_WEBHOOK_SECRET
    )
    if not is_valid:
        return signature_error_response(request)

    # ---- 2. Parse payload ----
    try:
        payload: dict = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.error(
            "webhook_payload_parse_error",
            error=str(exc),
            request_id=request_id,
        )
        # Gecersiz payload — retry anlamsiz, 200 dondur
        return JSONResponse(
            status_code=200,
            content={"status": "error", "detail": "Invalid payload format"},
        )

    # Event bilgilerini cikar
    event_id: str | None = payload.get("iyziEventId") or payload.get("paymentId")
    event_type: str | None = payload.get("iyziEventType") or payload.get("status")
    payment_external_id: str | None = payload.get("paymentId")

    if not event_id or not event_type:
        logger.warning(
            "webhook_missing_fields",
            payload_keys=list(payload.keys()),
            request_id=request_id,
        )
        return JSONResponse(
            status_code=200,
            content={"status": "error", "detail": "Missing required fields"},
        )

    logger.info(
        "webhook_received",
        event_id=event_id,
        event_type=event_type,
        payment_external_id=payment_external_id,
        request_id=request_id,
    )

    # ---- 3-6. DB transaction: dedup + state update ----
    async with async_session_factory() as session, session.begin():
        # --- 3. Inbox dedup ---
        inbox_event = await _inbox_service.receive_event(
            session=session,
            event_id=event_id,
            source="iyzico",
            event_type=f"payment.{event_type}",
            payload=payload,
        )

        # --- 4. Duplicate → skip ---
        if inbox_event is None:
            logger.info(
                "webhook_duplicate_skipped",
                event_id=event_id,
                request_id=request_id,
            )
            return JSONResponse(
                status_code=200,
                content={"status": "ok", "detail": "Duplicate event, skipped"},
            )

        # --- 5. Payment status guncelle ---
        new_status: str | None = _IYZICO_STATUS_MAP.get(event_type)

        if payment_external_id and new_status:
            try:
                await _update_payment_and_subscription(
                    session=session,
                    external_id=payment_external_id,
                    new_status=new_status,
                    event_type=event_type,
                    payload=payload,
                    request_id=request_id,
                )
            except Exception as exc:
                # Islem hatasi olsa bile 200 dondur — retry onleme
                # Hata loglanir, manual intervention veya retry-queue ile cozulur
                logger.error(
                    "webhook_processing_error",
                    event_id=event_id,
                    error=str(exc),
                    request_id=request_id,
                    exc_info=True,
                )
                # Transaction rollback — begin() context manager halleder
                return JSONResponse(
                    status_code=200,
                    content={"status": "error", "detail": "Processing error logged"},
                )
        else:
            logger.info(
                "webhook_unmapped_event",
                event_type=event_type,
                event_id=event_id,
                request_id=request_id,
            )

    # ---- 6. Basarili ----
    return JSONResponse(
        status_code=200,
        content={"status": "ok"},
    )


async def _update_payment_and_subscription(
    session,
    external_id: str,
    new_status: str,
    event_type: str,
    payload: dict,
    request_id: str | None,
) -> None:
    """
    Payment ve ilgili Subscription'i gunceller.

    Status mapping:
        success  → Payment.completed  + Subscription.active
        failure  → Payment.failed     + Subscription.past_due (+payment_failed_count)
        refund   → Payment.refunded   + Subscription.cancelled
    """
    now = datetime.now(UTC)

    # --- Payment bul ---
    result = await session.execute(
        select(Payment).where(Payment.external_id == external_id)
    )
    payment: Payment | None = result.scalar_one_or_none()

    if payment is None:
        logger.warning(
            "webhook_payment_not_found",
            external_id=external_id,
            request_id=request_id,
        )
        return

    # --- Payment guncelle ---
    old_payment_status = payment.status

    payment.status = new_status
    payment.external_status = event_type
    payment.metadata_ = {**payment.metadata_, "last_webhook": payload}

    if new_status == "completed":
        payment.paid_at = now
        payment.error_message = None
    elif new_status == "failed":
        payment.error_message = payload.get("errorMessage") or payload.get("errorCode")
    elif new_status == "refunded":
        payment.refunded_at = now

    logger.info(
        "payment_status_updated",
        payment_id=str(payment.id),
        external_id=external_id,
        old_status=old_payment_status,
        new_status=new_status,
        request_id=request_id,
    )

    # --- Subscription guncelle ---
    result = await session.execute(
        select(Subscription).where(Subscription.id == payment.subscription_id)
    )
    subscription: Subscription | None = result.scalar_one_or_none()

    if subscription is None:
        logger.warning(
            "webhook_subscription_not_found",
            subscription_id=str(payment.subscription_id),
            request_id=request_id,
        )
        return

    if new_status == "completed":
        subscription.status = "active"
        subscription.last_payment_at = now
        subscription.payment_failed_count = 0
    elif new_status == "failed":
        subscription.payment_failed_count += 1
        subscription.status = "past_due"
    elif new_status == "refunded":
        subscription.status = "cancelled"

    logger.info(
        "subscription_status_updated",
        subscription_id=str(subscription.id),
        new_status=subscription.status,
        payment_failed_count=subscription.payment_failed_count,
        request_id=request_id,
    )
