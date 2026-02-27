"""
Emlak Teknoloji Platformu - Telegram Auth Bridge

Telegram hesap baglama (deep link) mekanizmasinin is mantigi.

Akis:
    1. Web panel: Kullanici POST /telegram/link → generate_link_token()
       → Redis'e token kaydedilir (15dk TTL), deep link URL dondurulur.
    2. Telegram: Kullanici deep link'e tiklar → bot /start {token} alir
       → verify_and_link() → token Redis'te dogrulanir, tek kullanimlik silinir,
       User.telegram_chat_id guncellenir.
    3. Web panel: DELETE /telegram/link → unlink()
       → User.telegram_chat_id = None yapilir.

Guvenlik:
    - Token: secrets.token_urlsafe(32) — 256-bit entropi
    - TTL: 15 dakika (Redis EXPIRE)
    - Tek kullanimlik: verify_and_link() basarili olunca Redis'ten silinir
    - telegram_chat_id UNIQUE constraint — ayni chat birden fazla hesaba baglanamaz

Referans: TASK-039
"""

from __future__ import annotations

import secrets
import uuid
from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select, update

from src.models.user import User

if TYPE_CHECKING:
    from redis.asyncio import Redis
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

logger = structlog.get_logger(__name__)

# ================================================================
# Sabitler
# ================================================================

_TOKEN_PREFIX = "telegram:link:"
_TOKEN_TTL_SECONDS = 900  # 15 dakika
_TOKEN_BYTE_LENGTH = 32  # 256-bit entropi


# ================================================================
# TelegramAuthBridge
# ================================================================


class TelegramAuthBridge:
    """
    Telegram hesap baglama koprusu.

    Redis uzerinde tek kullanimlik token yonetimi ve
    SQLAlchemy uzerinde User.telegram_chat_id guncelleme islemlerini yurutur.

    Args:
        redis_client: redis.asyncio.Redis instance'i (DB 0 — cache).
        db_session_factory: SQLAlchemy async_sessionmaker (DI ile saglanir).
    """

    def __init__(
        self,
        redis_client: Redis,
        db_session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._redis = redis_client
        self._db_session_factory = db_session_factory

    # ================================================================
    # Public — Token Uretme
    # ================================================================

    async def generate_link_token(self, user_id: uuid.UUID) -> str:
        """
        Tek kullanimlik baglanti token'i uretir ve Redis'e kaydeder.

        Redis key: telegram:link:{token} → value: user_id (str)
        TTL: 15 dakika

        Ayni kullanici birden fazla token uretebilir — onceki token'lar
        TTL'e kadar gecerli kalir. verify_and_link() ilk gecerli token'i
        kullanir ve siler.

        Args:
            user_id: Baglanti kuracak kullanicinin UUID'si.

        Returns:
            Uretilen token string'i (URL-safe, 43 karakter).

        Raises:
            redis.RedisError: Redis baglanti hatasi.
        """
        token = secrets.token_urlsafe(_TOKEN_BYTE_LENGTH)
        key = f"{_TOKEN_PREFIX}{token}"

        await self._redis.set(key, str(user_id), ex=_TOKEN_TTL_SECONDS)

        logger.info(
            "telegram_link_token_generated",
            user_id=str(user_id),
            token_prefix=token[:8],
            ttl_seconds=_TOKEN_TTL_SECONDS,
        )

        return token

    # ================================================================
    # Public — Token Dogrulama + Hesap Baglama
    # ================================================================

    async def verify_and_link(self, token: str, chat_id: str) -> bool:
        """
        Token'i dogrular ve kullanicinin telegram_chat_id'sini gunceller.

        Akis:
            1. Redis'ten token degerini al (user_id)
            2. Token yoksa veya suresi dolmussa → False
            3. Token bulunduysa HEMEN sil (tek kullanimlik garanti)
            4. User.telegram_chat_id = chat_id olarak guncelle
            5. Basarili → True, basarisiz → False

        KRITIK: Token silme islem ONCE yapilir (adim 3), DB guncelleme
        basarisiz olsa bile token tekrar kullanilamaz. Bu, replay attack'i
        engeller.

        Args:
            token: Deep link ile gelen baglanti token'i.
            chat_id: Telegram chat ID (bot ile kullanici arasi sohbet).

        Returns:
            True: Baglama basarili.
            False: Token gecersiz, suresi dolmus veya DB guncelleme basarisiz.
        """
        key = f"{_TOKEN_PREFIX}{token}"

        # 1. Redis'ten token degerini al
        user_id_str: str | None = await self._redis.get(key)

        if user_id_str is None:
            logger.warning(
                "telegram_link_token_invalid",
                token_prefix=token[:8] if token else "empty",
            )
            return False

        # 2. Token'i HEMEN sil — tek kullanimlik garanti
        await self._redis.delete(key)

        # 3. user_id parse et
        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            logger.error(
                "telegram_link_token_invalid_user_id",
                user_id_str=user_id_str,
                token_prefix=token[:8],
            )
            return False

        # 4. User.telegram_chat_id guncelle
        try:
            async with self._db_session_factory() as session:
                result = await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .values(telegram_chat_id=chat_id)
                )
                await session.commit()

                if result.rowcount == 0:  # type: ignore[union-attr]
                    logger.error(
                        "telegram_link_user_not_found",
                        user_id=str(user_id),
                        chat_id=chat_id,
                    )
                    return False

        except Exception as exc:
            logger.error(
                "telegram_link_db_error",
                user_id=str(user_id),
                chat_id=chat_id,
                error=str(exc),
                exc_info=True,
            )
            return False

        logger.info(
            "telegram_link_success",
            user_id=str(user_id),
            chat_id=chat_id,
        )
        return True

    # ================================================================
    # Public — Hesap Baglantisini Kaldirma
    # ================================================================

    async def unlink(self, user_id: uuid.UUID) -> bool:
        """
        Kullanicinin Telegram baglantisini kaldirir.

        User.telegram_chat_id = None olarak guncellenir.

        Args:
            user_id: Baglantisi kaldirilacak kullanicinin UUID'si.

        Returns:
            True: Baglanti kaldirildi.
            False: Kullanici bulunamadi veya zaten baglanti yok.
        """
        try:
            async with self._db_session_factory() as session:
                result = await session.execute(
                    update(User)
                    .where(User.id == user_id)
                    .where(User.telegram_chat_id.isnot(None))
                    .values(telegram_chat_id=None)
                )
                await session.commit()

                if result.rowcount == 0:  # type: ignore[union-attr]
                    logger.warning(
                        "telegram_unlink_no_link",
                        user_id=str(user_id),
                    )
                    return False

        except Exception as exc:
            logger.error(
                "telegram_unlink_db_error",
                user_id=str(user_id),
                error=str(exc),
                exc_info=True,
            )
            return False

        logger.info(
            "telegram_unlink_success",
            user_id=str(user_id),
        )
        return True

    # ================================================================
    # Public — Chat ID ile Kullanici Sorgulama
    # ================================================================

    async def get_user_by_chat_id(self, chat_id: str) -> User | None:
        """
        Telegram chat ID'si ile bagli kullaniciyi getirir.

        Args:
            chat_id: Telegram chat ID.

        Returns:
            User instance'i veya None (baglanti yoksa).
        """
        try:
            async with self._db_session_factory() as session:
                result = await session.execute(
                    select(User).where(User.telegram_chat_id == chat_id)
                )
                return result.scalar_one_or_none()

        except Exception as exc:
            logger.error(
                "telegram_get_user_by_chat_id_error",
                chat_id=chat_id,
                error=str(exc),
                exc_info=True,
            )
            return None
