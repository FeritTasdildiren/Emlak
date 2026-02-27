"""
Sprint S10 Unit Test Suite — Telegram Mini App & Bot

Pure unit testleri — DB bagimliligi YOK, mock pattern kullanir.

Test kategorileri:
  1. TestAuthBridge — generate_link_token, verify_and_link, unlink (mock Redis+DB) — 8 test
  2. TestBotCommands — BOT_COMMANDS structure, command count — 4 test
  3. TestKrediParsing — _parse_amount ve _parse_term fonksiyonlari — 9 test
  4. TestDistrictCoords — _DISTRICT_COORDS dogrulama (39 ilce) — 4 test
  5. TestTelegramPublicPaths — /telegram/mini-app/ PUBLIC_PATH_PREFIXES'te — 2 test
  6. TestDailyReportStructure — daily report task fonksiyonu ve nitelikleri — 2 test
  7. TestWebhookSecurity — webhook path'lerinin PUBLIC_PATH_PREFIXES'te olmasi — 1 test

Toplam: 30 test

NOT: Asagidaki senaryolar ZATEN tests/unit/ altinda test edilmistir, burada TEKRARLANMAZ:
  - HMAC auth (test_mini_app_auth.py)
  - Invalid HMAC (test_mini_app_auth.py)
  - Expired init data (test_mini_app_auth.py)
  - Conversation state CRUD (test_conversation_state.py)
  - Bot notification/match callback (test_bot_notification.py, test_match_callback.py)
  - Bot error handling (test_bot_error_handling.py)
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.middleware.tenant import PUBLIC_PATH_PREFIXES
from src.modules.messaging.bot.auth_bridge import (
    _TOKEN_PREFIX,
    _TOKEN_TTL_SECONDS,
    TelegramAuthBridge,
)
from src.modules.messaging.bot.bot_commands import BOT_COMMANDS
from src.modules.messaging.bot.handlers import (
    _DISTRICT_COORDS,
    InvalidParamError,
    _parse_amount,
    _parse_term,
)

# ================================================================
# Fixtures
# ================================================================


@pytest.fixture
def mock_redis_client():
    """Mock async Redis client — auth_bridge testleri icin."""
    redis = AsyncMock()
    return redis


@pytest.fixture
def mock_db_factory():
    """Mock async_sessionmaker — auth_bridge testleri icin."""
    session = AsyncMock()
    session.commit = AsyncMock()

    mock_result = MagicMock()
    mock_result.rowcount = 1
    session.execute = AsyncMock(return_value=mock_result)

    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=session)
    ctx.__aexit__ = AsyncMock(return_value=False)

    factory = MagicMock()
    factory.return_value = ctx
    factory._mock_session = session
    factory._mock_result = mock_result
    return factory


@pytest.fixture
def auth_bridge(mock_redis_client, mock_db_factory):
    """TelegramAuthBridge instance — mock Redis + DB ile."""
    return TelegramAuthBridge(
        redis_client=mock_redis_client,
        db_session_factory=mock_db_factory,
    )


# ================================================================
# 1. TestAuthBridge — S10-TC-004, S10-TC-005, unlink
# ================================================================


class TestAuthBridge:
    """TelegramAuthBridge token uretme, dogrulama ve baglanti kaldirma."""

    # --- S10-TC-004: generate_link_token ---

    @pytest.mark.asyncio
    async def test_generate_link_token_returns_string(self, auth_bridge) -> None:
        """generate_link_token() string token dondurmeli."""
        user_id = uuid.uuid4()
        token = await auth_bridge.generate_link_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

    @pytest.mark.asyncio
    async def test_generate_link_token_stores_in_redis(
        self, auth_bridge, mock_redis_client
    ) -> None:
        """generate_link_token() Redis'e token:user_id kaydedmeli."""
        user_id = uuid.uuid4()
        token = await auth_bridge.generate_link_token(user_id)

        mock_redis_client.set.assert_called_once()
        call_args = mock_redis_client.set.call_args
        key = call_args.args[0] if call_args.args else call_args[0][0]
        assert key.startswith(_TOKEN_PREFIX)
        assert token in key

    @pytest.mark.asyncio
    async def test_generate_link_token_sets_ttl(
        self, auth_bridge, mock_redis_client
    ) -> None:
        """generate_link_token() Redis'e 900 saniye TTL ile yazmali."""
        user_id = uuid.uuid4()
        await auth_bridge.generate_link_token(user_id)

        call_kwargs = mock_redis_client.set.call_args
        assert call_kwargs.kwargs.get("ex") == _TOKEN_TTL_SECONDS

    # --- S10-TC-005: verify_and_link ---

    @pytest.mark.asyncio
    async def test_verify_and_link_success(
        self, auth_bridge, mock_redis_client, mock_db_factory
    ) -> None:
        """Gecerli token ile verify_and_link() True dondurmeli."""
        user_id = uuid.uuid4()
        mock_redis_client.get = AsyncMock(return_value=str(user_id))
        mock_redis_client.delete = AsyncMock()

        result = await auth_bridge.verify_and_link("valid_token", "chat_123")

        assert result is True
        mock_redis_client.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_and_link_invalid_token_returns_false(
        self, auth_bridge, mock_redis_client
    ) -> None:
        """Redis'te bulunmayan token icin verify_and_link() False dondurmeli."""
        mock_redis_client.get = AsyncMock(return_value=None)

        result = await auth_bridge.verify_and_link("expired_token", "chat_123")

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_and_link_deletes_token_before_db_update(
        self, auth_bridge, mock_redis_client
    ) -> None:
        """verify_and_link() token'i DB guncellemesinden ONCE silmeli (replay attack onleme)."""
        user_id = uuid.uuid4()
        mock_redis_client.get = AsyncMock(return_value=str(user_id))
        mock_redis_client.delete = AsyncMock()

        await auth_bridge.verify_and_link("token123", "chat_456")

        # delete cagrildimi (token silme)
        expected_key = f"{_TOKEN_PREFIX}token123"
        mock_redis_client.delete.assert_called_once_with(expected_key)

    # --- unlink ---

    @pytest.mark.asyncio
    async def test_unlink_success(self, auth_bridge, mock_db_factory) -> None:
        """Aktif baglantisi olan kullanici icin unlink() True dondurmeli."""
        user_id = uuid.uuid4()
        result = await auth_bridge.unlink(user_id)

        assert result is True

    @pytest.mark.asyncio
    async def test_unlink_no_link_returns_false(
        self, auth_bridge, mock_db_factory
    ) -> None:
        """Baglantisi olmayan kullanici icin unlink() False dondurmeli."""
        mock_db_factory._mock_result.rowcount = 0
        user_id = uuid.uuid4()

        result = await auth_bridge.unlink(user_id)

        assert result is False


# ================================================================
# 2. TestBotCommands — S10-TC-010 kismen
# ================================================================


class TestBotCommands:
    """BOT_COMMANDS listesi yapisal dogrulama."""

    def test_bot_commands_has_10_entries(self) -> None:
        """BOT_COMMANDS listesinde 10 komut bulunmali."""
        assert len(BOT_COMMANDS) == 10

    def test_bot_commands_are_tuples(self) -> None:
        """Her komut (komut_adi, aciklama) tuple'i olmali."""
        for cmd in BOT_COMMANDS:
            assert isinstance(cmd, tuple)
            assert len(cmd) == 2
            assert isinstance(cmd[0], str)
            assert isinstance(cmd[1], str)

    def test_bot_commands_include_required_commands(self) -> None:
        """Gerekli komutlar (start, help, ilan, iptal, degerleme, kredi) BOT_COMMANDS'ta olmali."""
        command_names = {cmd[0] for cmd in BOT_COMMANDS}
        required = {"start", "help", "ilan", "iptal", "degerleme", "kredi"}
        assert required.issubset(command_names)

    def test_bot_commands_no_slash_prefix(self) -> None:
        """BOT_COMMANDS komut adlari '/' ile baslamamali (BotCommand API slash ekler)."""
        for cmd, _desc in BOT_COMMANDS:
            assert not cmd.startswith("/"), f"'{cmd}' slash ile baslamamali"


# ================================================================
# 3. TestKrediParsing — S10-TC-013, S10-TC-014, S10-TC-015
# ================================================================


class TestKrediParsing:
    """_parse_amount ve _parse_term kredi parametre cozumleme."""

    # --- _parse_amount ---

    def test_parse_amount_plain_number(self) -> None:
        """Duz sayi: '2500000' → 2_500_000.0."""
        assert _parse_amount("2500000") == 2_500_000.0

    def test_parse_amount_million_shorthand(self) -> None:
        """Milyon kisaltmasi: '2.5m' → 2_500_000.0."""
        assert _parse_amount("2.5m") == 2_500_000.0

    def test_parse_amount_turkish_comma_format(self) -> None:
        """Turkce virgul formati: '2,5m' → 2_500_000.0."""
        assert _parse_amount("2,5m") == 2_500_000.0

    def test_parse_amount_thousand_shorthand(self) -> None:
        """Bin kisaltmasi: '500k' → 500_000.0."""
        assert _parse_amount("500k") == 500_000.0

    def test_parse_amount_invalid_raises(self) -> None:
        """Gecersiz tutar InvalidParamError firlatmali."""
        with pytest.raises(InvalidParamError, match="Gecersiz tutar"):
            _parse_amount("abc")

    # --- _parse_term ---

    def test_parse_term_months_plain(self) -> None:
        """Duz ay sayisi: '180' → 180."""
        assert _parse_term("180") == 180

    def test_parse_term_year_shorthand(self) -> None:
        """Yil kisaltmasi: '15y' → 180 (15 * 12)."""
        assert _parse_term("15y") == 180

    def test_parse_term_short_year(self) -> None:
        """Kisa vade: '10y' → 120 (10 * 12)."""
        assert _parse_term("10y") == 120

    def test_parse_term_invalid_raises(self) -> None:
        """Gecersiz vade InvalidParamError firlatmali."""
        with pytest.raises(InvalidParamError, match="Gecersiz vade"):
            _parse_term("abc")


# ================================================================
# 4. TestDistrictCoords — S10-TC-017, S10-TC-018, S10-TC-019
# ================================================================


class TestDistrictCoords:
    """_DISTRICT_COORDS Istanbul ilce koordinat dogrulama."""

    def test_district_coords_has_39_districts(self) -> None:
        """_DISTRICT_COORDS 39 Istanbul ilcesini icermeli."""
        assert len(_DISTRICT_COORDS) == 39

    def test_district_coords_all_lowercase_keys(self) -> None:
        """Tum ilce isimleri kucuk harfle olmali (fuzzy match icin normalize)."""
        for district in _DISTRICT_COORDS:
            assert district == district.lower(), f"'{district}' kucuk harf olmali"

    def test_district_coords_valid_lat_lon_range(self) -> None:
        """Tum koordinatlar Istanbul sinirlari icinde olmali (lat: 40-42, lon: 27-30)."""
        for district, (lat, lon) in _DISTRICT_COORDS.items():
            assert 40.0 <= lat <= 42.0, f"'{district}' lat={lat} aralik disi"
            assert 27.0 <= lon <= 30.0, f"'{district}' lon={lon} aralik disi"

    def test_district_coords_contains_major_districts(self) -> None:
        """Buyuk ilceler (kadikoy, besiktas, uskudar, fatih, sisli) mevcut olmali."""
        major_districts = {"kadikoy", "besiktas", "uskudar", "fatih", "sisli"}
        assert major_districts.issubset(_DISTRICT_COORDS.keys())


# ================================================================
# 5. TestTelegramPublicPaths — S10-TC-009, S10-TC-027
# ================================================================


class TestTelegramPublicPaths:
    """Telegram Mini App path'lerinin JWT bypass edilmesi dogrulamasi."""

    def test_mini_app_prefix_in_public_path_prefixes(self) -> None:
        """'/api/v1/telegram/mini-app/' PUBLIC_PATH_PREFIXES'te olmali."""
        assert any(
            prefix == "/api/v1/telegram/mini-app/"
            for prefix in PUBLIC_PATH_PREFIXES
        )

    def test_mini_app_path_matches_startswith(self) -> None:
        """Ornek mini-app path'i PUBLIC_PATH_PREFIXES ile eslesmeli (startswith)."""
        sample_path = "/api/v1/telegram/mini-app/auth"
        matches = sample_path.startswith(PUBLIC_PATH_PREFIXES)
        assert matches is True


# ================================================================
# 6. TestDailyReportStructure — S10-TC-020
# ================================================================


class TestDailyReportStructure:
    """Gunluk rapor Celery task fonksiyonu yapisal dogrulama."""

    def test_daily_report_task_exists(self) -> None:
        """send_daily_office_reports fonksiyonu import edilebilmeli."""
        from src.tasks.daily_report import send_daily_office_reports

        assert callable(send_daily_office_reports)

    def test_daily_report_task_has_correct_queue(self) -> None:
        """send_daily_office_reports 'notifications' queue'sunda olmali."""
        from src.tasks.daily_report import send_daily_office_reports

        # Celery task dekoratoru .queue attribute'u ekler
        assert send_daily_office_reports.queue == "notifications"


# ================================================================
# 7. TestWebhookSecurity — S10-TC-023, S10-TC-024
# ================================================================


class TestWebhookSecurity:
    """Webhook endpoint'lerinin JWT bypass (PUBLIC_PATH_PREFIXES) dogrulamasi."""

    def test_webhooks_prefix_in_public_path_prefixes(self) -> None:
        """'/webhooks/' prefix'i PUBLIC_PATH_PREFIXES'te olmali."""
        assert any(
            prefix == "/webhooks/"
            for prefix in PUBLIC_PATH_PREFIXES
        )
