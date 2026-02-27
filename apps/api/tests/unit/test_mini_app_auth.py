"""
TASK-141: Mini App Auth Unit Tests

Telegram Mini App HMAC-SHA256 initData dogrulama testleri.
Telegram API / DB bagimsiz — mock-based.

Kapsam:
    - HMAC-SHA256 imza dogrulama (gecerli/gecersiz)
    - Suresi dolmus initData (auth_date + 5dk TTL)
    - Hash parametresi eksik
    - auth_date eksik / gecersiz format
    - Bos initData / bos bot_token
    - User bilgisi parse (JSON → dict)
    - get_or_create_user_from_telegram: mevcut kullanici / yeni kullanici (hata)
"""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from unittest.mock import AsyncMock, MagicMock
from urllib.parse import urlencode

import pytest

from src.modules.messaging.bot.mini_app_auth import (
    _INIT_DATA_TTL_SECONDS,
    get_or_create_user_from_telegram,
    validate_init_data,
)

# ================================================================
# Helper: Gecerli initData Uretici
# ================================================================

BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"


def _build_init_data(
    bot_token: str = BOT_TOKEN,
    auth_date: int | None = None,
    user: dict | None = None,
    extra_params: dict | None = None,
) -> str:
    """
    Test icin gecerli (HMAC-signed) initData query string olusturur.

    Args:
        bot_token: Bot token.
        auth_date: Unix timestamp (varsayilan: simdiki zaman).
        user: Telegram user dict (varsayilan: test user).
        extra_params: Ek query parametreleri.

    Returns:
        HMAC-SHA256 imzali initData query string.
    """
    if auth_date is None:
        auth_date = int(time.time())

    if user is None:
        user = {
            "id": 987654321,
            "first_name": "Test",
            "last_name": "User",
            "username": "testuser",
        }

    params: dict[str, str] = {
        "auth_date": str(auth_date),
        "user": json.dumps(user),
    }
    if extra_params:
        params.update(extra_params)

    # data_check_string: sorted key=value, newline ile birlestir
    data_check_string = "\n".join(
        f"{key}={params[key]}" for key in sorted(params.keys())
    )

    # secret_key = HMAC-SHA256("WebAppData", bot_token)
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=bot_token.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    # hash = HMAC-SHA256(secret_key, data_check_string)
    computed_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).hexdigest()

    params["hash"] = computed_hash
    return urlencode(params)


# ================================================================
# validate_init_data Tests
# ================================================================


class TestValidateInitData:
    """validate_init_data() HMAC-SHA256 dogrulama testleri."""

    def test_valid_init_data_passes(self):
        """Gecerli HMAC imzali initData basariyla dogrulanmali."""
        init_data = _build_init_data()
        result = validate_init_data(init_data, BOT_TOKEN)

        assert "auth_date" in result
        assert "user" in result

    def test_valid_init_data_returns_parsed_user(self):
        """Dogrulama sonrasi user alani dict olarak parse edilmeli."""
        user = {"id": 111, "first_name": "Ahmet", "last_name": "Y."}
        init_data = _build_init_data(user=user)
        result = validate_init_data(init_data, BOT_TOKEN)

        assert isinstance(result["user"], dict)
        assert result["user"]["id"] == 111
        assert result["user"]["first_name"] == "Ahmet"

    def test_invalid_hash_raises_value_error(self):
        """Gecersiz hash ile ValueError firlatilmali."""
        init_data = _build_init_data()
        # Hash'i boz
        init_data = init_data.replace("hash=", "hash=TAMPERED")

        with pytest.raises(ValueError, match="imzasi gecersiz"):
            validate_init_data(init_data, BOT_TOKEN)

    def test_wrong_bot_token_raises_value_error(self):
        """Yanlis bot token ile hash dogrulamasi basarisiz olmali."""
        init_data = _build_init_data(bot_token=BOT_TOKEN)

        with pytest.raises(ValueError, match="imzasi gecersiz"):
            validate_init_data(init_data, "WRONG:TOKEN")

    def test_expired_init_data_raises_value_error(self):
        """Suresi dolmus initData (auth_date + 5dk) ValueError firlatmali."""
        expired_time = int(time.time()) - _INIT_DATA_TTL_SECONDS - 60
        init_data = _build_init_data(auth_date=expired_time)

        with pytest.raises(ValueError, match="suresi dolmus"):
            validate_init_data(init_data, BOT_TOKEN)

    def test_missing_hash_raises_value_error(self):
        """Hash parametresi olmayan initData ValueError firlatmali."""
        # hash olmadan query string olustur
        params = {
            "auth_date": str(int(time.time())),
            "user": json.dumps({"id": 111, "first_name": "Test"}),
        }
        init_data = urlencode(params)

        with pytest.raises(ValueError, match="hash"):
            validate_init_data(init_data, BOT_TOKEN)

    def test_missing_auth_date_raises_value_error(self):
        """auth_date olmayan initData ValueError firlatmali."""
        # auth_date olmadan imza olusturmak icin trick:
        # once auth_date ile olustur, sonra auth_date'i cikar
        # Bu durumda hash gecersiz olacak ama auth_date kontrolu once gelir
        # Aslinda hash parametresi olan ama auth_date olmayan bir string yapalim
        params = {"user": json.dumps({"id": 111})}
        data_check_string = "\n".join(
            f"{key}={params[key]}" for key in sorted(params.keys())
        )
        secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
        computed_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        params["hash"] = computed_hash
        init_data = urlencode(params)

        with pytest.raises(ValueError, match="auth_date"):
            validate_init_data(init_data, BOT_TOKEN)

    def test_empty_init_data_raises_value_error(self):
        """Bos initData ValueError firlatmali."""
        with pytest.raises(ValueError, match="bos olamaz"):
            validate_init_data("", BOT_TOKEN)

    def test_empty_bot_token_raises_value_error(self):
        """Bos bot_token ValueError firlatmali."""
        init_data = _build_init_data()
        with pytest.raises(ValueError, match="bos olamaz"):
            validate_init_data(init_data, "")

    def test_ttl_constant_is_300_seconds(self):
        """TTL sabiti 300 saniye (5 dakika) olmali."""
        assert _INIT_DATA_TTL_SECONDS == 300

    def test_just_within_ttl_passes(self):
        """TTL sinirinda (tam 5dk) gecerli olmali."""
        # 4 dakika 59 saniye once — hala gecerli
        auth_date = int(time.time()) - _INIT_DATA_TTL_SECONDS + 10
        init_data = _build_init_data(auth_date=auth_date)
        result = validate_init_data(init_data, BOT_TOKEN)
        assert result is not None


# ================================================================
# get_or_create_user_from_telegram Tests
# ================================================================


class TestGetOrCreateUserFromTelegram:
    """get_or_create_user_from_telegram() kullanici bulma/olusturma testleri."""

    @pytest.mark.asyncio
    async def test_existing_user_returned(self):
        """Mevcut kullanici (telegram_id ile) dogrudan dondurulmeli."""
        mock_user = MagicMock()
        mock_user.id = "user-uuid-123"
        mock_user.telegram_id = 12345

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_user

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        telegram_user = {"id": 12345, "first_name": "Ali"}
        result = await get_or_create_user_from_telegram(telegram_user, mock_db)

        assert result == mock_user
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_new_user_raises_value_error(self):
        """
        Yeni kullanici icin ValueError firlatilmali.

        Mevcut implementasyon yeni kullanici olusturmak yerine
        'platformda kayitli degil' hatasi verir.
        """
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None

        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_result

        telegram_user = {"id": 99999, "first_name": "Yeni"}

        with pytest.raises(ValueError, match="platformda kayitli degil"):
            await get_or_create_user_from_telegram(telegram_user, mock_db)

    @pytest.mark.asyncio
    async def test_missing_telegram_id_raises_value_error(self):
        """Telegram user dict'inde 'id' yoksa ValueError firlatilmali."""
        mock_db = AsyncMock()

        telegram_user = {"first_name": "NoId"}

        with pytest.raises(ValueError, match="id"):
            await get_or_create_user_from_telegram(telegram_user, mock_db)
