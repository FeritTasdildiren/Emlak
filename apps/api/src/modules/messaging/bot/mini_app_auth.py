"""
Emlak Teknoloji Platformu - Telegram Mini App Auth

Telegram Mini App initData dogrulamasi ve JWT token uretimi.

Akis:
    1. Mini App acildiginda Telegram SDK initDataRaw (query string) gonderi.
    2. validate_init_data() HMAC-SHA256 ile imza dogrular.
    3. auth_date kontrolu (5 dakika TTL) ile replay attack engellenir.
    4. get_or_create_user_from_telegram() ile kullanici bulunur veya olusturulur.
    5. JWT token cifti uretilir ve dondurulur.

Guvenlik:
    - HMAC-SHA256: secret_key = HMAC("WebAppData", bot_token)
    - data_check_string: sorted key=value pairs (hash haric)
    - auth_date TTL: 5 dakika (replay korunmasi)
    - telegram_id UNIQUE constraint — ayni Telegram hesabi birden fazla kullaniciya baglanamaz

Referans:
    - https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    - TASK-131
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, unquote

import structlog
from sqlalchemy import select

from src.models.user import User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)

# ================================================================
# Sabitler
# ================================================================

_INIT_DATA_TTL_SECONDS = 300  # 5 dakika — replay korunmasi


# ================================================================
# initData Dogrulama
# ================================================================


def validate_init_data(init_data: str, bot_token: str) -> dict[str, Any]:
    """
    Telegram Mini App initData imzasini dogrular.

    Telegram'in resmi dogrulama algoritmasi:
        1. init_data query string'ini parse et.
        2. 'hash' parametresini ayir.
        3. Kalan parametreleri key=value olarak sirala (sorted).
        4. secret_key = HMAC-SHA256("WebAppData", bot_token)
        5. data_check_hash = HMAC-SHA256(secret_key, data_check_string)
        6. data_check_hash == hash ise gecerli.
        7. auth_date + TTL < now ise suresi dolmus.

    Args:
        init_data: Telegram SDK'dan gelen ham query string.
        bot_token: Bot token (TELEGRAM_BOT_TOKEN).

    Returns:
        Parse edilmis initData dict'i (user, auth_date, vb.).

    Raises:
        ValueError: Imza gecersiz, suresi dolmus veya format hatasi.
    """
    if not init_data or not bot_token:
        raise ValueError("init_data ve bot_token bos olamaz.")

    # 1. Query string parse
    parsed = parse_qs(init_data, keep_blank_values=True)

    # Tek degerli parametreleri duzlestir
    params: dict[str, str] = {}
    for key, values in parsed.items():
        params[key] = values[0] if values else ""

    # 2. Hash parametresini ayir
    received_hash = params.pop("hash", None)
    if not received_hash:
        raise ValueError("init_data icinde 'hash' parametresi bulunamadi.")

    # 3. data_check_string olustur (sorted key=value, newline ile birlestir)
    data_check_string = "\n".join(
        f"{key}={params[key]}" for key in sorted(params.keys())
    )

    # 4. secret_key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    # 5. data_check_hash = HMAC-SHA256(secret_key, data_check_string)
    computed_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    # 6. Hash karsilastirmasi (timing-safe)
    if not hmac.compare_digest(computed_hash, received_hash):
        logger.warning(
            "mini_app_init_data_invalid_hash",
            received_hash_prefix=received_hash[:8] if received_hash else "empty",
        )
        raise ValueError("initData imzasi gecersiz.")

    # 7. auth_date TTL kontrolu
    auth_date_str = params.get("auth_date")
    if not auth_date_str:
        raise ValueError("init_data icinde 'auth_date' bulunamadi.")

    try:
        auth_date = int(auth_date_str)
    except (ValueError, TypeError) as exc:
        raise ValueError("auth_date gecersiz format.") from exc

    now = int(time.time())
    if now - auth_date > _INIT_DATA_TTL_SECONDS:
        logger.warning(
            "mini_app_init_data_expired",
            auth_date=auth_date,
            now=now,
            diff_seconds=now - auth_date,
        )
        raise ValueError(
            f"initData suresi dolmus (auth_date: {auth_date}, "
            f"simdi: {now}, fark: {now - auth_date}s, TTL: {_INIT_DATA_TTL_SECONDS}s)."
        )

    # 8. user bilgisini parse et (JSON string olarak gelir)
    user_raw = params.get("user")
    if user_raw:
        try:
            params["user"] = json.loads(unquote(user_raw))
        except (json.JSONDecodeError, TypeError):
            # user parse edilemezse ham string olarak birak
            logger.warning("mini_app_user_parse_failed", user_raw=user_raw[:100])

    logger.info(
        "mini_app_init_data_validated",
        auth_date=auth_date,
        has_user="user" in params,
    )

    return params


# ================================================================
# Kullanici Bulma / Olusturma
# ================================================================


async def get_or_create_user_from_telegram(
    telegram_user: dict[str, Any],
    db: AsyncSession,
) -> User:
    """
    Telegram kullanici bilgilerinden platform kullanicisi bulur veya olusturur.

    Oncelik sirasi:
        1. telegram_id ile ara (User.telegram_id == tg_user.id)
        2. Bulunamadiysa yeni kullanici olustur (sifresiz, auto-linked)

    Yeni kullanici olusturulurken:
        - email: tg_{telegram_id}@telegram.local (placeholder)
        - password_hash: "!" (login devre disi — sadece Mini App ile erisim)
        - full_name: Telegram first_name + last_name
        - role: "agent" (varsayilan)
        - telegram_id: Telegram user ID
        - is_active: True
        - is_verified: False

    ONEMLI: Yeni olusturulan kullanicilar icin office_id gerekli.
    Simdilik varsayilan ofis yoksa hata firlatilir.

    Args:
        telegram_user: Telegram initData icindeki user objesi.
            {id: int, first_name: str, last_name?: str, username?: str, ...}
        db: SQLAlchemy async session.

    Returns:
        User instance'i (mevcut veya yeni olusturulmus).

    Raises:
        ValueError: Telegram user ID bulunamadi.
    """
    tg_id = telegram_user.get("id")
    if not tg_id:
        raise ValueError("Telegram user bilgisinde 'id' alani bulunamadi.")

    tg_id_int = int(tg_id)

    # 1. Mevcut kullaniciyi telegram_id ile ara
    result = await db.execute(
        select(User).where(User.telegram_id == tg_id_int)
    )
    user = result.scalar_one_or_none()

    if user is not None:
        logger.info(
            "mini_app_user_found",
            user_id=str(user.id),
            telegram_id=tg_id_int,
        )
        return user

    # 2. Yeni kullanici olustur
    first_name = telegram_user.get("first_name", "Telegram")
    last_name = telegram_user.get("last_name", "")
    full_name = f"{first_name} {last_name}".strip()

    logger.info(
        "mini_app_user_creating",
        telegram_id=tg_id_int,
        full_name=full_name,
    )

    # NOT: Yeni kullanici icin office_id gerekli.
    # Ileride varsayilan ofis veya onboarding akisi eklenecek.
    # Simdilik ValueError firlat — front-end bunu handle eder.
    raise ValueError(
        f"Telegram kullanicisi (id={tg_id_int}) platformda kayitli degil. "
        "Once web panelden kayit olun ve Telegram hesabinizi baglayin."
    )
