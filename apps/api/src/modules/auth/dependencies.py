"""
Emlak Teknoloji Platformu - Auth Dependencies

FastAPI dependency injection: token dogrulama, aktif kullanici, rol kontrolu.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Annotated, Any

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine

import structlog
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.exceptions import AuthenticationError, PermissionDenied
from src.database import get_db_session
from src.models.user import User
from src.modules.auth import service as auth_service
from src.modules.auth.token_blacklist import TokenBlacklist

logger = structlog.get_logger()

# ---------- Security Scheme ----------
# auto_error=False: token yoksa 403 yerine None doner, biz 401 firlatiyoruz
_bearer_scheme = HTTPBearer(auto_error=False)


# ---------- Current User ----------


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    db: Annotated[Any, Depends(get_db_session)],
) -> User:
    """
    Bearer token'dan mevcut kullaniciyi cikarir.

    Akis:
    1. Authorization header'dan token al
    2. JWT decode et (exp, type kontrol)
    3. Payload'dan user_id al
    4. DB'den kullaniciyi getir

    Raises:
        AuthenticationError: Token yok, gecersiz veya kullanici bulunamadi.
    """
    if credentials is None:
        raise AuthenticationError(detail="Kimlik dogrulama bilgisi gerekli.")

    token = credentials.credentials

    # Token blacklist kontrolü
    redis_client = request.app.state.redis_client
    blacklist = TokenBlacklist(redis_client)
    if await blacklist.is_blacklisted(token):
        logger.warning("blacklisted_token_used", token_suffix=token[-8:])
        raise AuthenticationError(detail="Oturumunuz sona erdi (blacklist). Lütfen tekrar giriş yapın.")

    payload = auth_service.decode_token(token)

    # Token tipi kontrolu — sadece access token kabul edilir
    token_type = payload.get("type")
    if token_type != "access":
        raise AuthenticationError(detail="Gecersiz token tipi. Access token gerekli.")

    # User ID'yi payload'dan al
    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        raise AuthenticationError(detail="Token payload gecersiz.")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as e:
        raise AuthenticationError(detail="Token payload gecersiz.") from e

    # DB'den kullaniciyi getir
    user = await auth_service.get_user_by_id(db, user_id)
    if user is None:
        raise AuthenticationError(detail="Kullanici bulunamadi.")

    return user


# ---------- Active User ----------


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """
    Aktif kullaniciyi dondurur. Pasif hesaplar 403 alir.

    Raises:
        PermissionDenied: Hesap deaktif edilmis.
    """
    if not current_user.is_active:
        raise PermissionDenied(detail="Hesabiniz deaktif edilmis. Yonetici ile iletisime gecin.")

    return current_user


# ---------- Role-Based Access Control ----------


def require_role(
    *allowed_roles: str,
) -> Callable[..., Coroutine[Any, Any, User]]:
    """
    Rol tabanli erisim kontrolu dependency factory.

    Kullanim:
        @router.get("/admin", dependencies=[Depends(require_role("platform_admin"))])
        async def admin_panel(): ...

        @router.get("/office", dependencies=[Depends(require_role("office_admin", "office_owner"))])
        async def office_panel(): ...

    Raises:
        PermissionDenied: Kullanicinin rolu izin verilen roller arasinda degil.
    """

    async def _role_checker(
        current_user: Annotated[User, Depends(get_current_active_user)],
    ) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                "role_access_denied",
                user_id=str(current_user.id),
                user_role=current_user.role,
                required_roles=list(allowed_roles),
            )
            raise PermissionDenied(
                detail=f"Bu islem icin gereken roller: {', '.join(allowed_roles)}. "
                f"Mevcut rolunuz: {current_user.role}.",
            )
        return current_user

    return _role_checker


# ---------- Annotated Types (convenience) ----------
CurrentUser = Annotated[User, Depends(get_current_user)]
ActiveUser = Annotated[User, Depends(get_current_active_user)]
