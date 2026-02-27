"""
Emlak Teknoloji Platformu - Auth Service

Sifre hashing, JWT token islemleri, kullanici CRUD ve sifre sifirlama.
Tum is mantigi burada izole edilir — router'dan bagimsiz test edilebilir.
"""

from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import bcrypt
import structlog
from jose import JWTError, jwt
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from src.config import settings
from src.core.exceptions import AuthenticationError, ConflictError, ValidationError
from src.models.user import User

if TYPE_CHECKING:
    import uuid

    from redis.asyncio import Redis
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.auth.schemas import RegisterRequest

logger = structlog.get_logger()

# ---------- Password Hashing ----------
# bcrypt dogrudan kullanilir — passlib, bcrypt>=4.1 ile uyumsuz (abandoned lib).


def hash_password(password: str) -> str:
    """Plaintext sifreyi bcrypt ile hash'ler (cost factor=12)."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Plaintext sifreyi hash ile karsilastirir. Timing-safe."""
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


# ---------- JWT Token ----------


def create_access_token(data: dict) -> str:
    """
    Access token olusturur.

    Payload'a `sub` (user_id), `type` ve `exp` eklenir.
    Omur: JWT_ACCESS_TOKEN_EXPIRE_MINUTES (default 30dk).
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(data: dict) -> str:
    """
    Refresh token olusturur.

    Omur: JWT_REFRESH_TOKEN_EXPIRE_DAYS (default 7 gun).
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """
    JWT token'i decode eder.

    Raises:
        AuthenticationError: Token gecersiz veya suresi dolmus.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError as e:
        logger.warning("jwt_decode_failed", error=str(e))
        raise AuthenticationError(detail="Token gecersiz veya suresi dolmus.") from e


# ---------- User Operations ----------


async def register_user(
    db: AsyncSession,
    request: RegisterRequest,
    office_id: uuid.UUID,
) -> User:
    """
    Yeni kullanici olusturur.

    - Email unique check (DB constraint + explicit)
    - Password bcrypt hash
    - Default role: agent

    NOT: Register public endpoint'tir — TenantMiddleware SET LOCAL yapmaz.
    RLS FORCE aktif oldugu icin, bu fonksiyon kendi SET LOCAL'ini yapar
    (platform_admin bypass + office_id).

    Raises:
        ConflictError: Email zaten kayitli.
    """
    # Public endpoint — RLS bypass icin platform_admin + office_id SET LOCAL
    # asyncpg parameterized SET LOCAL desteklemiyor, f-string kullanilir
    await db.execute(text("SET LOCAL app.current_user_role = 'platform_admin'"))
    await db.execute(text(f"SET LOCAL app.current_office_id = '{office_id}'"))

    # Email duplicate kontrolu (DB seviyesinde de var ama guzel hata mesaji icin)
    existing = await db.execute(
        select(User).where(User.email == request.email)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(detail=f"Bu e-posta adresi zaten kayitli: {request.email}")

    user = User(
        email=request.email,
        password_hash=hash_password(request.password),
        full_name=request.full_name,
        phone=request.phone,
        role="agent",
        office_id=office_id,
    )

    try:
        db.add(user)
        await db.flush()
    except IntegrityError as e:
        await db.rollback()
        logger.warning("register_integrity_error", email=request.email, error=str(e))
        raise ConflictError(detail=f"Bu e-posta adresi zaten kayitli: {request.email}") from e

    logger.info("user_registered", user_id=str(user.id), email=user.email)
    return user


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User:
    """
    Kullaniciyi email + sifre ile dogrular.

    Basarili giris sonrasi last_login_at guncellenir.

    NOT: Login public endpoint'tir — TenantMiddleware SET LOCAL yapmaz.
    RLS FORCE aktif oldugu icin, platform_admin bypass gerekir.

    Raises:
        AuthenticationError: Email bulunamadi veya sifre yanlis.
    """
    # Public endpoint — RLS bypass icin platform_admin + dummy office_id SET LOCAL
    # NOT: office_id dummy UUID olmali — RLS policy'deki ::uuid cast bos string'de hata verir
    await db.execute(text("SET LOCAL app.current_user_role = 'platform_admin'"))
    await db.execute(text("SET LOCAL app.current_office_id = '00000000-0000-0000-0000-000000000000'"))

    result = await db.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one_or_none()

    if user is None:
        # Timing attack'a karsi: dummy hash compare yap ama sonucu kullanma
        _dummy_hash = "$2b$12$LJ3m4ys3Lf2YEMoUMkYkzOzr0qVfcTqHdY5Xp7LzWzg5KYhI/xyW"
        bcrypt.checkpw(b"dummy", _dummy_hash.encode("utf-8"))
        raise AuthenticationError(detail="E-posta veya sifre hatali.")

    if not verify_password(password, user.password_hash):
        raise AuthenticationError(detail="E-posta veya sifre hatali.")

    # last_login_at guncelle — UPDATE icin office_id SET LOCAL gerekir (RLS USING filtresi)
    await db.execute(text(f"SET LOCAL app.current_office_id = '{user.office_id}'"))
    user.last_login_at = datetime.now(UTC)
    await db.flush()

    logger.info("user_authenticated", user_id=str(user.id), email=user.email)
    return user


async def get_user_by_id(
    db: AsyncSession, user_id: uuid.UUID, *, bypass_rls: bool = False
) -> User | None:
    """
    Kullaniciyi UUID ile getirir.

    Args:
        bypass_rls: True ise platform_admin SET LOCAL yapar (public endpoint'ler icin).
    """
    if bypass_rls:
        await db.execute(text("SET LOCAL app.current_user_role = 'platform_admin'"))
        await db.execute(text("SET LOCAL app.current_office_id = '00000000-0000-0000-0000-000000000000'"))
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(
    db: AsyncSession, email: str, *, bypass_rls: bool = False
) -> User | None:
    """
    Kullaniciyi email ile getirir.

    Args:
        bypass_rls: True ise platform_admin SET LOCAL yapar (public endpoint'ler icin).
    """
    if bypass_rls:
        await db.execute(text("SET LOCAL app.current_user_role = 'platform_admin'"))
        await db.execute(text("SET LOCAL app.current_office_id = '00000000-0000-0000-0000-000000000000'"))
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


# ---------- Password Reset ----------

_PASSWORD_RESET_PREFIX = "password_reset:"


def _generate_reset_token() -> str:
    """Kriptografik olarak guvenli, URL-safe reset token olusturur (43 karakter)."""
    return secrets.token_urlsafe(32)


async def create_password_reset_token(redis: Redis, user_id: str) -> str:
    """
    Sifre sifirlama tokeni olusturur ve Redis'e kaydeder.

    Redis key: password_reset:{token}
    Value: user_id (str)
    TTL: PASSWORD_RESET_TOKEN_EXPIRE_MINUTES (default 30dk)

    Tek kullanimlik: token dogrulama sonrasi Redis'ten silinir.

    Returns:
        Olusturulan reset token (URL-safe).
    """
    token = _generate_reset_token()
    key = f"{_PASSWORD_RESET_PREFIX}{token}"
    ttl_seconds = settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES * 60

    await redis.setex(key, ttl_seconds, user_id)

    logger.info("password_reset_token_created", user_id=user_id, ttl_minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
    return token


async def verify_password_reset_token(redis: Redis, token: str) -> str | None:
    """
    Reset token'i dogrular ve user_id dondurur.

    Token gecerliyse Redis'ten silinir (tek kullanimlik).

    Returns:
        user_id (str) veya None (gecersiz/suresi dolmus token).
    """
    key = f"{_PASSWORD_RESET_PREFIX}{token}"

    user_id = await redis.get(key)
    if user_id is None:
        logger.warning("password_reset_token_invalid", token_suffix=token[-8:])
        return None

    # Tek kullanimlik: token'i sil
    await redis.delete(key)
    logger.info("password_reset_token_verified", user_id=user_id, token_suffix=token[-8:])
    return user_id


async def reset_user_password(
    db: AsyncSession,
    redis: Redis,
    token: str,
    new_password: str,
) -> None:
    """
    Reset token ile kullanici sifresini gunceller.

    Akis:
        1. Token'i dogrula (Redis) → user_id
        2. Kullaniciyi DB'den getir
        3. Yeni sifreyi bcrypt ile hashle
        4. DB'ye kaydet

    Raises:
        AuthenticationError: Token gecersiz veya suresi dolmus.
        AuthenticationError: Kullanici bulunamadi.
    """
    user_id_str = await verify_password_reset_token(redis, token)
    if user_id_str is None:
        raise AuthenticationError(detail="Sifirlama tokeni gecersiz veya suresi dolmus.")

    import uuid as _uuid

    try:
        user_id = _uuid.UUID(user_id_str)
    except ValueError as e:
        raise AuthenticationError(detail="Gecersiz token verisi.") from e

    user = await get_user_by_id(db, user_id, bypass_rls=True)
    if user is None:
        raise AuthenticationError(detail="Kullanici bulunamadi.")

    user.password_hash = hash_password(new_password)
    await db.flush()

    logger.info("password_reset_success", user_id=user_id_str)


async def change_user_password(
    db: AsyncSession,
    user: User,
    current_password: str,
    new_password: str,
) -> None:
    """
    Login olmus kullanicinin sifresini degistirir (mevcut sifre dogrulamasi ile).

    Raises:
        AuthenticationError: Mevcut sifre hatali.
        ValidationError: Yeni sifre mevcut sifre ile ayni.
    """
    if not verify_password(current_password, user.password_hash):
        raise AuthenticationError(detail="Mevcut sifre hatali.")

    if verify_password(new_password, user.password_hash):
        raise ValidationError(detail="Yeni sifre mevcut sifre ile ayni olamaz.")

    user.password_hash = hash_password(new_password)
    await db.flush()

    logger.info("password_changed", user_id=str(user.id))
