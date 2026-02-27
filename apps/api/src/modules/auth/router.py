"""
Emlak Teknoloji Platformu - Auth Router

JWT tabanli auth endpoint'leri: register, login, refresh, me.

Prefix: /api/v1/auth
"""

from __future__ import annotations

import uuid

import structlog
from fastapi import APIRouter, Request, status

from src.config import settings
from src.core.exceptions import AuthenticationError
from src.core.rate_limit import limiter
from src.dependencies import DBSession
from src.modules.audit.audit_service import AuditService
from src.modules.auth import service as auth_service
from src.modules.auth.dependencies import ActiveUser
from src.modules.auth.schemas import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    LogoutRequest,
    RefreshRequest,
    RegisterRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserResponse,
)
from src.modules.auth.token_blacklist import TokenBlacklist
from src.modules.messaging.templates.engine import MessageTemplateEngine

logger = structlog.get_logger()

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["auth"],
)


# ---------- POST /register ----------


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Yeni kullanici kaydi",
    description="E-posta, sifre ve ad ile yeni kullanici olusturur.",
)
@limiter.limit("3/minute")
async def register(
    request: Request,
    payload: RegisterRequest,
    db: DBSession,
) -> UserResponse:
    """
    Yeni kullanici kaydeder.

    - Email unique check yapilir (409 Conflict)
    - Sifre bcrypt ile hash'lenir
    - Default rol: agent
    - office_id body'den alinir (gerekli)
    """
    # office_id: body'den gelir. Yoksa hata.
    if payload.office_id is None:
        raise AuthenticationError(detail="Kayit icin office_id gereklidir.")

    try:
        office_uuid = uuid.UUID(payload.office_id)
    except ValueError as e:
        raise AuthenticationError(detail="Gecersiz office_id formati.") from e

    user = await auth_service.register_user(db, payload, office_uuid)

    return UserResponse(
        id=str(user.id),
        email=user.email,
        full_name=user.full_name,
        phone=user.phone,
        role=user.role,
        office_id=str(user.office_id),
        avatar_url=user.avatar_url,
        is_active=user.is_active,
        is_verified=user.is_verified,
        preferred_channel=user.preferred_channel,
    )


# ---------- POST /login ----------


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Kullanici girisi",
    description="E-posta ve sifre ile JWT token cifti uretir.",
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    payload: LoginRequest,
    db: DBSession,
) -> TokenResponse:
    """
    Kullaniciyi dogrular ve JWT token cifti dondurur.

    - Email + sifre kontrolu
    - last_login_at guncellenir
    - Access token (30dk) + Refresh token (7 gun)
    """
    user = await auth_service.authenticate_user(db, payload.email, payload.password)

    # JWT payload'a office_id ve role eklenmeli — TenantMiddleware bu alanlari okur
    token_data = {
        "sub": str(user.id),
        "office_id": str(user.office_id),
        "role": user.role,
    }
    access_token = auth_service.create_access_token(token_data)
    refresh_token = auth_service.create_refresh_token(token_data)

    logger.info("login_success", user_id=str(user.id))

    # KVKK Audit: Login kaydı
    await AuditService.log_action(
        db=db,
        user_id=user.id,
        office_id=user.office_id,
        action="LOGIN",
        entity_type="User",
        entity_id=str(user.id),
        request=request,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


# ---------- POST /refresh ----------


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Token yenileme",
    description="Refresh token ile yeni access/refresh token cifti uretir.",
)
@limiter.limit("10/minute")
async def refresh(
    request: Request,
    payload: RefreshRequest,
    db: DBSession,
) -> TokenResponse:
    """
    Refresh token'i dogrular ve yeni token cifti uretir.

    - Sadece 'refresh' tipli token'lar kabul edilir
    - Kullanicinin hala DB'de mevcut oldugu kontrol edilir
    - Yeni access + refresh token cifti dondurulur (token rotation)
    """
    payload_data = auth_service.decode_token(payload.refresh_token)

    # Token tipi kontrolu — sadece refresh token kabul edilir
    token_type = payload_data.get("type")
    if token_type != "refresh":
        raise AuthenticationError(detail="Gecersiz token tipi. Refresh token gerekli.")

    # User ID'yi payload'dan al
    user_id_str: str | None = payload_data.get("sub")
    if user_id_str is None:
        raise AuthenticationError(detail="Token payload gecersiz.")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as e:
        raise AuthenticationError(detail="Token payload gecersiz.") from e

    # Kullanicinin hala mevcut oldugunu kontrol et
    # NOT: Refresh public endpoint — RLS bypass gerekli (TenantMiddleware SET LOCAL yapmaz)
    user = await auth_service.get_user_by_id(db, user_id, bypass_rls=True)
    if user is None:
        raise AuthenticationError(detail="Kullanici bulunamadi.")

    if not user.is_active:
        raise AuthenticationError(detail="Hesap deaktif edilmis.")

    # Yeni token cifti uret (rotation)
    token_data = {
        "sub": str(user.id),
        "office_id": str(user.office_id),
        "role": user.role,
    }
    access_token = auth_service.create_access_token(token_data)
    new_refresh_token = auth_service.create_refresh_token(token_data)

    logger.info("token_refreshed", user_id=str(user.id))

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


# ---------- POST /logout ----------


@router.post(
    "/logout",
    summary="Cikis yap",
    description="Access ve (opsiyonel) refresh token'i blacklist'e ekleyerek oturumu kapatir.",
)
async def logout(
    request: Request,
    payload: LogoutRequest,
    current_user: ActiveUser,
    db: DBSession,
) -> dict:
    """
    Oturumu kapatir.

    - Mevcut access token'i blacklist'e ekler
    - Varsa refresh token'i blacklist'e ekler
    """
    # 1. Access Token'i al
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise AuthenticationError(detail="Access token bulunamadi.")

    access_token = auth_header.split(" ")[1]

    # 2. Blacklist instance
    blacklist = TokenBlacklist(request.app.state.redis_client)

    # 3. Access Token'i ekle (30 dk TTL varsayilan)
    # Gercekte exp claim'inden hesaplamak daha dogru ama simdilik sabit 30dk (config'den)
    await blacklist.add(access_token, settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60)

    # 4. Refresh Token'i ekle (varsa)
    if payload.refresh_token:
        # Refresh token omru 7 gun
        await blacklist.add(
            payload.refresh_token, settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
        )

    logger.info("logout_success", user_id=str(current_user.id))

    # KVKK Audit: Logout kaydı
    await AuditService.log_action(
        db=db,
        user_id=current_user.id,
        office_id=current_user.office_id,
        action="LOGOUT",
        entity_type="User",
        entity_id=str(current_user.id),
        request=request,
    )

    return {"message": "Basariyla cikis yapildi."}


# ---------- GET /me ----------


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Mevcut kullanici bilgileri",
    description="Bearer token ile kimlik dogrulanmis aktif kullanicinin bilgilerini dondurur.",
)
async def me(current_user: ActiveUser) -> UserResponse:
    """
    Authenticated kullanicinin profil bilgilerini dondurur.

    Requires: Bearer access token (Authorization header).
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        role=current_user.role,
        office_id=str(current_user.office_id),
        avatar_url=current_user.avatar_url,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        preferred_channel=current_user.preferred_channel,
    )


# ---------- POST /forgot-password ----------


@router.post(
    "/forgot-password",
    summary="Sifre sifirlama talebi",
    description="E-posta adresine sifre sifirlama linki gonderir.",
)
@limiter.limit("3/hour")
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,
    db: DBSession,
) -> dict:
    """
    Sifre sifirlama akisini baslatir.

    Guvenlik:
    - Email var/yok bilgisi sizdirilmaz (her durumda ayni mesaj)
    - Rate limit: 3 istek/saat/IP
    - Token: secrets.token_urlsafe(32), Redis'te 30dk TTL
    - Token tek kullanimlik (dogrulama sonrasi silinir)
    """
    # Her durumda ayni mesaj — email enumeration koruması
    success_msg = (
        "E-posta adresinize sifre sifirlama linki gonderildi. "
        "Lutfen gelen kutunuzu kontrol edin."
    )

    user = await auth_service.get_user_by_email(db, payload.email, bypass_rls=True)
    if user is None:
        # Email yoksa sessizce basarili don — timing attack'a karsi
        logger.info("forgot_password_email_not_found", email=payload.email)
        return {"message": success_msg}

    if not user.is_active:
        logger.warning("forgot_password_inactive_user", user_id=str(user.id))
        return {"message": success_msg}

    # Redis'ten reset token olustur
    redis = request.app.state.redis_client
    token = await auth_service.create_password_reset_token(redis, str(user.id))

    # Sifirlama linki
    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={token}"

    # Email template render & log (gercek email gonderimi messaging service ile entegre edilir)
    try:
        engine = MessageTemplateEngine()
        content = engine.render(
            template_id="password_reset",
            locale="tr",
            name=user.full_name,
            reset_url=reset_url,
            expire_minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES,
        )
        logger.info(
            "password_reset_email_prepared",
            user_id=str(user.id),
            email=user.email,
            template_text_length=len(content.text),
        )
    except FileNotFoundError:
        logger.warning(
            "password_reset_template_not_found",
            user_id=str(user.id),
        )

    logger.info("forgot_password_requested", user_id=str(user.id), email=user.email)
    return {"message": success_msg}


# ---------- POST /reset-password ----------


@router.post(
    "/reset-password",
    summary="Sifre sifirlama onay",
    description="Token ve yeni sifre ile sifreyi gunceller.",
)
@limiter.limit("5/hour")
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,
    db: DBSession,
) -> dict:
    """
    Sifre sifirlama token'i ile yeni sifreyi ayarlar.

    - Token Redis'ten dogrulanir (tek kullanimlik)
    - Yeni sifre bcrypt ile hash'lenir
    - Rate limit: 5 istek/saat/IP
    """
    redis = request.app.state.redis_client
    await auth_service.reset_user_password(db, redis, payload.token, payload.new_password)

    logger.info("password_reset_completed")
    return {"message": "Sifreniz basariyla guncellendi. Yeni sifrenizle giris yapabilirsiniz."}


# ---------- POST /change-password ----------


@router.post(
    "/change-password",
    summary="Sifre degistirme (login zorunlu)",
    description="Mevcut sifre ile dogrulama yaparak yeni sifre belirler.",
)
@limiter.limit("5/hour")
async def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: ActiveUser,
    db: DBSession,
) -> dict:
    """
    Login olmus kullanicinin sifresini degistirir.

    - Mevcut sifre dogrulanir
    - Yeni sifre mevcut sifre ile ayni olamaz
    - Rate limit: 5 istek/saat/IP
    - JWT (Bearer token) zorunlu
    """
    await auth_service.change_user_password(
        db, current_user, payload.current_password, payload.new_password
    )

    logger.info("password_changed_via_endpoint", user_id=str(current_user.id))
    return {"message": "Sifreniz basariyla degistirildi."}
