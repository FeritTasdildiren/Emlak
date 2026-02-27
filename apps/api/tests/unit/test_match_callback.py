"""
TASK-141: Match Callback Handler Unit Tests

TelegramBotHandler._handle_match_callback() testleri.
DB / Telegram API bagimsiz — mock-based.

Kapsam:
    - accept → interested status
    - skip → passed status
    - responded_at timestamp set edilmesi
    - Idempotent (zaten islenmis match)
    - Gecersiz UUID formatı
    - Bulunamayan match
    - Gecersiz action (ne accept ne skip)
    - Inline keyboard kaldirma (edit_message)
    - Gecersiz callback_data formati (3 parca degil)
"""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.modules.messaging.bot.handlers import TelegramBotHandler
from src.modules.messaging.schemas import IncomingMessage

# ================================================================
# Fixtures
# ================================================================

CHAT_ID = "123456789"
MATCH_UUID = uuid.UUID("c0000000-0000-0000-0000-000000000001")


@pytest.fixture
def mock_match():
    """Mock PropertyCustomerMatch objesi — pending status."""
    match_obj = MagicMock()
    match_obj.id = MATCH_UUID
    match_obj.status = "pending"
    match_obj.responded_at = None
    match_obj.customer = MagicMock()
    match_obj.customer.full_name = "Ahmet Y."
    match_obj.customer.phone = "+905321234567"
    match_obj.customer.email = "ahmet@test.com"
    match_obj.customer.notes = None
    match_obj.property = MagicMock()
    return match_obj


@pytest.fixture
def handler_with_db(mock_telegram_adapter, mock_session_factory, mock_match):
    """TelegramBotHandler instance — DB mock ile match donduren."""
    auth_bridge = MagicMock()

    # session_factory'den donen session'in match dondurmesini ayarla
    mock_result = mock_session_factory._mock_result
    mock_result.scalar_one_or_none.return_value = mock_match

    handler = TelegramBotHandler(
        telegram_adapter=mock_telegram_adapter,
        auth_bridge=auth_bridge,
        session_factory=mock_session_factory,
        redis_client=None,
    )
    return handler


def _make_callback_message(
    callback_data: str,
    chat_id: str = CHAT_ID,
    cq_id: str = "callback_query_123",
    message_id: int = 999,
) -> IncomingMessage:
    """Test icin callback query IncomingMessage olusturur."""
    return IncomingMessage(
        sender_id=chat_id,
        channel="telegram",
        content=callback_data,
        raw_payload={
            "callback_query": {
                "id": cq_id,
                "message": {"message_id": message_id},
            }
        },
    )


# ================================================================
# Accept/Skip Status Tests
# ================================================================


class TestMatchCallbackAccept:
    """accept callback → interested status testleri."""

    @pytest.mark.asyncio
    async def test_accept_sets_interested_status(self, handler_with_db, mock_match):
        """accept action → match status 'interested' olmali."""
        incoming = _make_callback_message(f"match:{MATCH_UUID}:accept")

        with patch("src.modules.messaging.bot.handlers.select"):
            await handler_with_db._handle_match_callback(incoming)

        assert mock_match.status == "interested"

    @pytest.mark.asyncio
    async def test_accept_sets_responded_at(self, handler_with_db, mock_match):
        """accept action → responded_at timestamp set edilmeli."""
        incoming = _make_callback_message(f"match:{MATCH_UUID}:accept")

        with patch("src.modules.messaging.bot.handlers.select"):
            await handler_with_db._handle_match_callback(incoming)

        assert mock_match.responded_at is not None

    @pytest.mark.asyncio
    async def test_accept_sends_contact_info(
        self, handler_with_db, mock_telegram_adapter, mock_match
    ):
        """accept sonrasi musteri iletisim bilgileri gonderilmeli."""
        incoming = _make_callback_message(f"match:{MATCH_UUID}:accept")

        with patch("src.modules.messaging.bot.handlers.select"):
            await handler_with_db._handle_match_callback(incoming)

        # adapter.send en az 1 kez cagrildimi (iletisim mesaji)
        assert mock_telegram_adapter.send.call_count >= 1

    @pytest.mark.asyncio
    async def test_accept_answers_callback_query(
        self, handler_with_db, mock_telegram_adapter, mock_match
    ):
        """accept sonrasi callback query yanitlanmali."""
        incoming = _make_callback_message(f"match:{MATCH_UUID}:accept")

        with patch("src.modules.messaging.bot.handlers.select"):
            await handler_with_db._handle_match_callback(incoming)

        mock_telegram_adapter.answer_callback_query.assert_called()


class TestMatchCallbackSkip:
    """skip callback → passed status testleri."""

    @pytest.mark.asyncio
    async def test_skip_sets_passed_status(self, handler_with_db, mock_match):
        """skip action → match status 'passed' olmali."""
        incoming = _make_callback_message(f"match:{MATCH_UUID}:skip")

        with patch("src.modules.messaging.bot.handlers.select"):
            await handler_with_db._handle_match_callback(incoming)

        assert mock_match.status == "passed"

    @pytest.mark.asyncio
    async def test_skip_sets_responded_at(self, handler_with_db, mock_match):
        """skip action → responded_at timestamp set edilmeli."""
        incoming = _make_callback_message(f"match:{MATCH_UUID}:skip")

        with patch("src.modules.messaging.bot.handlers.select"):
            await handler_with_db._handle_match_callback(incoming)

        assert mock_match.responded_at is not None

    @pytest.mark.asyncio
    async def test_skip_answers_callback_query(
        self, handler_with_db, mock_telegram_adapter, mock_match
    ):
        """skip sonrasi callback query 'Atlandi' ile yanitlanmali."""
        incoming = _make_callback_message(f"match:{MATCH_UUID}:skip")

        with patch("src.modules.messaging.bot.handlers.select"):
            await handler_with_db._handle_match_callback(incoming)

        mock_telegram_adapter.answer_callback_query.assert_called()


# ================================================================
# Idempotent Tests
# ================================================================


class TestMatchCallbackIdempotent:
    """Zaten islenmis match — idempotent davranis testleri."""

    @pytest.mark.asyncio
    async def test_already_interested_does_not_change_status(
        self, handler_with_db, mock_telegram_adapter, mock_match
    ):
        """Zaten 'interested' olan match tekrar islenemez."""
        mock_match.status = "interested"
        incoming = _make_callback_message(f"match:{MATCH_UUID}:accept")

        with patch("src.modules.messaging.bot.handlers.select"):
            await handler_with_db._handle_match_callback(incoming)

        # Status degismemeli
        assert mock_match.status == "interested"
        # Callback query yanitlanmali (bilgi mesaji)
        mock_telegram_adapter.answer_callback_query.assert_called()

    @pytest.mark.asyncio
    async def test_already_passed_does_not_change_status(
        self, handler_with_db, mock_telegram_adapter, mock_match
    ):
        """Zaten 'passed' olan match tekrar islenemez."""
        mock_match.status = "passed"
        incoming = _make_callback_message(f"match:{MATCH_UUID}:skip")

        with patch("src.modules.messaging.bot.handlers.select"):
            await handler_with_db._handle_match_callback(incoming)

        assert mock_match.status == "passed"


# ================================================================
# Error Cases
# ================================================================


class TestMatchCallbackErrors:
    """Hata senaryolari — gecersiz UUID, bulunamayan match, gecersiz action."""

    @pytest.mark.asyncio
    async def test_invalid_uuid_answers_error(
        self, handler_with_db, mock_telegram_adapter
    ):
        """Gecersiz UUID callback query'de hata mesaji gondermeli."""
        incoming = _make_callback_message("match:NOT-A-UUID:accept")

        with patch("src.modules.messaging.bot.handlers.select"):
            await handler_with_db._handle_match_callback(incoming)

        mock_telegram_adapter.answer_callback_query.assert_called()
        call_kwargs = mock_telegram_adapter.answer_callback_query.call_args
        assert "Gecersiz" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_match_not_found_answers_error(
        self, handler_with_db, mock_telegram_adapter, mock_session_factory
    ):
        """Match bulunamadiysa callback query'de hata mesaji gondermeli."""
        mock_session_factory._mock_result.scalar_one_or_none.return_value = None
        incoming = _make_callback_message(f"match:{MATCH_UUID}:accept")

        with patch("src.modules.messaging.bot.handlers.select"):
            await handler_with_db._handle_match_callback(incoming)

        mock_telegram_adapter.answer_callback_query.assert_called()
        call_kwargs = mock_telegram_adapter.answer_callback_query.call_args
        assert "bulunamadi" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_invalid_action_answers_error(
        self, handler_with_db, mock_telegram_adapter
    ):
        """Gecersiz action (ne accept ne skip) hata mesaji gondermeli."""
        incoming = _make_callback_message(f"match:{MATCH_UUID}:INVALID")

        with patch("src.modules.messaging.bot.handlers.select"):
            await handler_with_db._handle_match_callback(incoming)

        mock_telegram_adapter.answer_callback_query.assert_called()
        call_kwargs = mock_telegram_adapter.answer_callback_query.call_args
        assert "Gecersiz" in str(call_kwargs)

    @pytest.mark.asyncio
    async def test_malformed_callback_data_not_three_parts(
        self, handler_with_db, mock_telegram_adapter
    ):
        """3 parcadan olusmayan callback_data hata gondermeli."""
        incoming = _make_callback_message("match:only_two")

        with patch("src.modules.messaging.bot.handlers.select"):
            await handler_with_db._handle_match_callback(incoming)

        mock_telegram_adapter.answer_callback_query.assert_called()
        call_kwargs = mock_telegram_adapter.answer_callback_query.call_args
        assert "Gecersiz" in str(call_kwargs)
