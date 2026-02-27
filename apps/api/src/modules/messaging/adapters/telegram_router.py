"""
Emlak Teknoloji Platformu - Telegram Webhook Router

Telegram Bot API'den gelen webhook bildirimlerini isleyen FastAPI router.

Prefix: /webhooks/telegram
Guvenlik: PUBLIC endpoint (JWT gerektirmez — /webhooks/ prefix'i TenantMiddleware'de bypass)

Tasarim kararlari (payments/router.py referansi):
    - Webhook HER ZAMAN 200 dondurur.
      Telegram gecersiz yanit alirsa webhook'u deaktive edebilir — bu onlenir.
    - Hata durumlarinda loglayip 200 dondur, internal olarak coz.
    - Ileride inbox pattern ile idempotency eklenebilir (update_id bazli dedup).

Telegram webhook setup:
    Bot.set_webhook(url=settings.TELEGRAM_WEBHOOK_URL) ile
    Telegram'a webhook URL'i bildirilir (lifespan startup'inda yapilir).
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import structlog
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

from src.config import settings

if TYPE_CHECKING:
    from src.modules.messaging.adapters.telegram import TelegramAdapter
    from src.modules.messaging.bot.handlers import TelegramBotHandler

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/webhooks/telegram",
    tags=["webhooks"],
)


@router.post(
    "",
    status_code=status.HTTP_200_OK,
    summary="Telegram webhook callback",
    description=(
        "Telegram Bot API'den gelen Update bildirimlerini isler. "
        "PUBLIC endpoint — JWT gerektirmez."
    ),
)
async def telegram_webhook(request: Request) -> JSONResponse:
    """
    Telegram webhook handler.

    Akis:
        1. Raw body al ve JSON parse et
        2. TelegramAdapter.handle_webhook() ile IncomingMessage'e donustur
        3. Her durumda 200 dondur (Telegram webhook deaktivasyon onleme)

    Hata senaryolari:
        - Adapter kayitli degil → 200 + log
        - Gecersiz JSON → 200 + log
        - Parse hatasi → 200 + log

    NOT: Is mantigi (mesaj isleme, yanit olusturma) ileride
    MessagingService entegrasyonu ile eklenecektir.
    """
    request_id = getattr(request.state, "request_id", None)

    # ---- 0. Secret Token Dogrulama (TASK-150) ----
    if settings.TELEGRAM_WEBHOOK_SECRET:
        received_secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
        if received_secret != settings.TELEGRAM_WEBHOOK_SECRET:
            logger.warning(
                "telegram_webhook_invalid_secret",
                detail="X-Telegram-Bot-Api-Secret-Token dogrulanamadi",
                request_id=request_id,
            )
            return JSONResponse(
                status_code=403,
                content={"status": "error", "detail": "Invalid secret token"},
            )

    # ---- 1. Adapter kontrolu ----
    adapter: TelegramAdapter | None = getattr(request.app.state, "telegram_adapter", None)
    if adapter is None:
        logger.error(
            "telegram_webhook_no_adapter",
            detail="TelegramAdapter app.state'te bulunamadi",
            request_id=request_id,
        )
        # 200 dondur — Telegram webhook'u deaktive etmesin
        return JSONResponse(
            status_code=200,
            content={"status": "error", "detail": "Adapter not configured"},
        )

    # ---- 2. Raw body al ve parse et ----
    try:
        raw_body = await request.body()
        payload: dict = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        logger.error(
            "telegram_webhook_parse_error",
            error=str(exc),
            request_id=request_id,
        )
        return JSONResponse(
            status_code=200,
            content={"status": "error", "detail": "Invalid payload format"},
        )

    update_id = payload.get("update_id")

    logger.info(
        "telegram_webhook_received",
        update_id=update_id,
        request_id=request_id,
    )

    # ---- 3. Handle webhook → IncomingMessage ----
    try:
        incoming_message = await adapter.handle_webhook(payload)

        logger.info(
            "telegram_webhook_processed",
            update_id=update_id,
            sender_id=incoming_message.sender_id,
            content_preview=incoming_message.content[:50] if incoming_message.content else "",
            request_id=request_id,
        )

        # ---- 3b. Bot handler'a yonlendir (komut isleme + echo) ----
        bot_handler: TelegramBotHandler | None = getattr(
            request.app.state, "telegram_bot_handler", None
        )
        if bot_handler is not None:
            await bot_handler.handle(incoming_message)
        else:
            logger.debug(
                "telegram_webhook_no_bot_handler",
                detail="TelegramBotHandler app.state'te bulunamadi, mesaj islenmedi",
                update_id=update_id,
                request_id=request_id,
            )

    except ValueError as exc:
        # Desteklenmeyen update tipi — loglayip gecir
        logger.warning(
            "telegram_webhook_unsupported_update",
            update_id=update_id,
            error=str(exc),
            request_id=request_id,
        )
    except Exception as exc:
        # Beklenmeyen hata — loglayip 200 dondur
        logger.error(
            "telegram_webhook_processing_error",
            update_id=update_id,
            error=str(exc),
            request_id=request_id,
            exc_info=True,
        )

    # ---- 4. Her durumda 200 ----
    return JSONResponse(
        status_code=200,
        content={"status": "ok"},
    )
