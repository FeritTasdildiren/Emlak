"""
Emlak Teknoloji Platformu - Telegram Router

Telegram hesap baglama/kaldirma/durum + Mini App auth API endpoint'leri.

Prefix: /api/v1/telegram
Guvenlik:
    - /link/* endpoint'leri: JWT ZORUNLU — aktif kullanici gerektirir.
    - /mini-app/auth: PUBLIC — initData dogrulamasi yeterli (JWT gerektirmez).

Endpoint'ler:
    POST   /link            — Baglanti linki uret (deep link URL)
    DELETE /link            — Baglanti kaldir (telegram_chat_id = None)
    GET    /link/status     — Baglanti durumu sorgula
    POST   /mini-app/auth   — Mini App initData → JWT token

Referans: TASK-039, TASK-131
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import structlog
from fastapi import APIRouter, Depends, Request

from src.config import settings
from src.core.exceptions import AuthenticationError, ConflictError, NotFoundError
from src.dependencies import DBSession
from src.modules.auth import service as auth_service
from src.modules.auth.dependencies import ActiveUser
from src.modules.messaging.bot.mini_app_auth import (
    get_or_create_user_from_telegram,
    validate_init_data,
)
from src.modules.messaging.bot.schemas import (
    LinkResponse,
    LinkStatusResponse,
    MiniAppAuthRequest,
    MiniAppAuthResponse,
    MiniAppUserResponse,
)

if TYPE_CHECKING:
    from src.modules.messaging.bot.auth_bridge import TelegramAuthBridge

logger = structlog.get_logger(__name__)


router = APIRouter(
    prefix="/api/v1/telegram",
    tags=["telegram"],
)


# ================================================================
# Helper — AuthBridge DI
# ================================================================


def _get_auth_bridge(request: Request) -> TelegramAuthBridge:
    """
    app.state uzerinden TelegramAuthBridge instance'ina erisir.

    Raises:
        RuntimeError: AuthBridge app.state'te bulunamadi
            (lifespan'de yapilandirilmamis).
    """
    auth_bridge: TelegramAuthBridge | None = getattr(
        request.app.state, "telegram_auth_bridge", None
    )
    if auth_bridge is None:
        raise RuntimeError(
            "TelegramAuthBridge app.state'te bulunamadi. "
            "Lifespan yapilandirmasini kontrol edin."
        )
    return auth_bridge


# ================================================================
# POST /link — Baglanti linki uret
# ================================================================


@router.post(
    "/link",
    response_model=LinkResponse,
    summary="Telegram baglanti linki olustur",
    description=(
        "Mevcut kullanici icin tek kullanimlik Telegram deep link token'i uretir. "
        "Token 15 dakika gecerlidir. Kullanici linke tikladiginda "
        "Telegram hesabi platforma baglanir."
    ),
)
async def create_link(
    current_user: ActiveUser,
    auth_bridge: Annotated[TelegramAuthBridge, Depends(_get_auth_bridge)],
) -> LinkResponse:
    """
    Telegram hesap baglama linki olusturur.

    Akis:
        1. Kullanicinin zaten bagli hesabi var mi kontrol et
        2. Token uret ve Redis'e kaydet
        3. Deep link URL olustur
        4. LinkResponse dondur

    Raises:
        ConflictError: Kullanicinin zaten bagli Telegram hesabi var.
    """
    # Zaten bagli mi kontrol et
    if current_user.telegram_chat_id is not None:
        raise ConflictError(
            detail="Telegram hesabiniz zaten bagli. "
            "Once mevcut baglantiyi kaldirin."
        )

    token = await auth_bridge.generate_link_token(current_user.id)

    # Deep link URL olustur
    bot_username = settings.TELEGRAM_BOT_USERNAME
    link_url = f"https://t.me/{bot_username}?start={token}"

    logger.info(
        "telegram_link_created",
        user_id=str(current_user.id),
    )

    return LinkResponse(
        link_url=link_url,
        token=token,
        expires_in=900,
    )


# ================================================================
# DELETE /link — Baglanti kaldir
# ================================================================


@router.delete(
    "/link",
    summary="Telegram baglantisini kaldir",
    description="Mevcut kullanicinin Telegram hesap baglantisini kaldirir.",
)
async def delete_link(
    current_user: ActiveUser,
    auth_bridge: Annotated[TelegramAuthBridge, Depends(_get_auth_bridge)],
) -> dict:
    """
    Telegram hesap baglantisini kaldirir.

    Raises:
        NotFoundError: Kullanicinin bagli Telegram hesabi yok.
    """
    success = await auth_bridge.unlink(current_user.id)

    if not success:
        raise NotFoundError(resource="Telegram baglantisi")

    logger.info(
        "telegram_link_deleted",
        user_id=str(current_user.id),
    )

    return {"status": "ok", "detail": "Telegram baglantisi kaldirildi."}


# ================================================================
# GET /link/status — Baglanti durumu
# ================================================================


@router.get(
    "/link/status",
    response_model=LinkStatusResponse,
    summary="Telegram baglanti durumu",
    description="Mevcut kullanicinin Telegram hesap baglanti durumunu dondurur.",
)
async def get_link_status(
    current_user: ActiveUser,
) -> LinkStatusResponse:
    """
    Telegram hesap baglanti durumunu sorgular.

    JWT'den alinan current_user uzerindeki telegram_chat_id alani kontrol edilir.
    Ek DB sorgusu gerekmez.
    """
    linked = current_user.telegram_chat_id is not None

    return LinkStatusResponse(
        linked=linked,
        telegram_chat_id=current_user.telegram_chat_id,
    )


# ================================================================
# POST /mini-app/auth — Mini App initData → JWT Token
# ================================================================


@router.post(
    "/mini-app/auth",
    response_model=MiniAppAuthResponse,
    summary="Mini App authentication",
    description=(
        "Telegram Mini App initData dogrulamasi yapar ve JWT token cifti uretir. "
        "PUBLIC endpoint — JWT gerektirmez, Telegram initData imzasi yeterlidir."
    ),
)
async def mini_app_auth(
    request: MiniAppAuthRequest,
    db: DBSession,
) -> MiniAppAuthResponse:
    """
    Telegram Mini App initData'yi dogrular ve JWT token uretir.

    Akis:
        1. initData HMAC-SHA256 imza dogrulamasi
        2. auth_date TTL kontrolu (5dk)
        3. Telegram user bilgisinden platform kullanicisi bul
        4. JWT access + refresh token cifti uret
        5. MiniAppAuthResponse dondur

    Guvenlik:
        - Bu endpoint PUBLIC'tir (JWT gerektirmez).
        - Kimlik dogrulamasi Telegram initData imzasi ile yapilir.
        - bot_token asla client'a gonderilmez — sadece server-side dogrulama.

    Raises:
        AuthenticationError: initData gecersiz, suresi dolmus veya kullanici bulunamadi.
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        logger.error("mini_app_auth_no_bot_token")
        raise AuthenticationError(
            detail="Telegram bot yapilandirmasi eksik. Lutfen yonetici ile iletisime gecin."
        )

    # 1. initData dogrula
    try:
        init_data = validate_init_data(request.init_data, bot_token)
    except ValueError as exc:
        logger.warning(
            "mini_app_auth_validation_failed",
            error=str(exc),
        )
        raise AuthenticationError(
            detail=f"Telegram dogrulama basarisiz: {exc}"
        ) from exc

    # 2. Telegram user bilgisini al
    telegram_user = init_data.get("user")
    if not telegram_user or not isinstance(telegram_user, dict):
        raise AuthenticationError(
            detail="initData icinde kullanici bilgisi bulunamadi."
        )

    # 3. Kullaniciyi bul veya olustur
    try:
        user = await get_or_create_user_from_telegram(telegram_user, db)
    except ValueError as exc:
        logger.warning(
            "mini_app_auth_user_error",
            telegram_id=telegram_user.get("id"),
            error=str(exc),
        )
        raise AuthenticationError(detail=str(exc)) from exc

    # 4. JWT token cifti uret
    token_data = {"sub": str(user.id), "office_id": str(user.office_id)}
    access_token = auth_service.create_access_token(token_data)
    refresh_token = auth_service.create_refresh_token(token_data)

    logger.info(
        "mini_app_auth_success",
        user_id=str(user.id),
        telegram_id=telegram_user.get("id"),
    )

    return MiniAppAuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=MiniAppUserResponse(
            id=str(user.id),
            full_name=user.full_name,
            role=user.role,
            avatar_url=user.avatar_url,
        ),
    )
