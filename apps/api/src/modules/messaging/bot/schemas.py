"""
Emlak Teknoloji Platformu - Telegram Bot Schemas

Telegram hesap baglama (deep link) islemleri icin Pydantic modelleri.

Kullanim:
    - LinkResponse: POST /telegram/link yaniti (deep link URL + token)
    - LinkStatusResponse: GET /telegram/link/status yaniti (baglanti durumu)
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LinkResponse(BaseModel):
    """
    Telegram hesap baglama linki yaniti.

    POST /telegram/link endpoint'i tarafindan dondurulur.
    Kullanici bu URL'i Telegram'da acarak hesabini baglar.
    """

    link_url: str = Field(
        ...,
        description="Telegram deep link URL'i (https://t.me/bot?start=token)",
    )
    token: str = Field(
        ...,
        description="Tek kullanimlik baglanti token'i",
    )
    expires_in: int = Field(
        default=900,
        description="Token gecerlilik suresi (saniye) — varsayilan 15 dakika",
    )


class LinkStatusResponse(BaseModel):
    """
    Telegram hesap baglanti durumu yaniti.

    GET /telegram/link/status endpoint'i tarafindan dondurulur.
    """

    linked: bool = Field(
        ...,
        description="Telegram hesabi bagli mi?",
    )
    telegram_chat_id: str | None = Field(
        default=None,
        description="Bagli Telegram chat ID (yoksa null)",
    )


# ================================================================
# Mini App Auth Schemas
# ================================================================


class MiniAppAuthRequest(BaseModel):
    """
    Mini App auth istegi.

    POST /telegram/mini-app/auth endpoint'ine gonderilir.
    init_data: Telegram SDK'dan gelen ham initDataRaw query string.
    """

    init_data: str = Field(
        ...,
        min_length=1,
        description="Telegram Mini App SDK'dan alinan initDataRaw string",
    )


class MiniAppUserResponse(BaseModel):
    """Mini App icin sadelesmis kullanici bilgileri."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(description="Kullanici UUID")
    full_name: str = Field(description="Ad soyad")
    role: str = Field(description="Kullanici rolu")
    avatar_url: str | None = Field(default=None, description="Profil fotografi URL")


class MiniAppAuthResponse(BaseModel):
    """
    Mini App auth yaniti.

    Basarili dogrulama sonrasi JWT token cifti ve kullanici bilgileri dondurulur.
    """

    access_token: str = Field(description="Access token (kisa omurlu)")
    refresh_token: str = Field(description="Refresh token (uzun omurlu)")
    token_type: str = Field(default="bearer", description="Token tipi")
    user: MiniAppUserResponse = Field(description="Kullanici bilgileri")
