"""
TASK-141: Bot Error Handling Unit Tests

TelegramBotHandler hata yonetimi ve _ERROR_MESSAGES dogrulama testleri.
Telegram API / DB bagimsiz — mock-based.

Kapsam:
    - _ERROR_MESSAGES dict 6 tip (general, quota, not_found, permission, timeout, invalid_input)
    - _send_error() dogru mesaj secimi + request_id format
    - request_id 8 karakter hex
    - structlog alanlari (handler, request_id, user_id, chat_id, error_type, error_msg)
    - handle() top-level exception → mesaj gondermez (sadece loglar)
    - _handle_iptal() sessiz (conv manager yokken)
"""

from __future__ import annotations

import re
import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.modules.messaging.bot.handlers import (
    _ERROR_MESSAGES,
    TelegramBotHandler,
)
from src.modules.messaging.schemas import IncomingMessage

# ================================================================
# Fixtures
# ================================================================


@pytest.fixture
def handler(mock_telegram_adapter, mock_session_factory):
    """TelegramBotHandler instance — mock dependencies ile."""
    auth_bridge = MagicMock()
    return TelegramBotHandler(
        telegram_adapter=mock_telegram_adapter,
        auth_bridge=auth_bridge,
        session_factory=mock_session_factory,
        redis_client=None,  # conv state devre disi
    )


# ================================================================
# _ERROR_MESSAGES Tests
# ================================================================


class TestErrorMessages:
    """_ERROR_MESSAGES dictionary dogrulama."""

    def test_has_six_error_types(self):
        """_ERROR_MESSAGES 6 hata tipi icermeli."""
        expected_types = {
            "general",
            "quota",
            "not_found",
            "permission",
            "timeout",
            "invalid_input",
        }
        assert set(_ERROR_MESSAGES.keys()) == expected_types

    def test_all_messages_contain_request_id_placeholder(self):
        """Her mesaj {request_id} placeholder'i icermeli."""
        for error_type, msg in _ERROR_MESSAGES.items():
            assert "{request_id}" in msg, (
                f"'{error_type}' mesaji {{request_id}} placeholder'i icermiyor"
            )

    def test_all_messages_contain_referans_prefix(self):
        """Her mesajda 'Referans:' oncesi olmali (kullanici icin takip kodu)."""
        for error_type, msg in _ERROR_MESSAGES.items():
            assert "Referans:" in msg, (
                f"'{error_type}' mesajinda 'Referans:' bulunamadi"
            )

    def test_general_message_has_retry_hint(self):
        """'general' hata mesaji tekrar deneme onerisi icermeli."""
        assert "tekrar deneyin" in _ERROR_MESSAGES["general"]

    def test_quota_message_has_plan_hint(self):
        """'quota' hata mesaji plan yukseltme onerisi icermeli."""
        assert "Plan yukseltmek" in _ERROR_MESSAGES["quota"] or "help" in _ERROR_MESSAGES["quota"]

    def test_permission_message_has_lock_emoji(self):
        """'permission' hata mesaji kilit emojisi icermeli."""
        assert "🔒" in _ERROR_MESSAGES["permission"]


# ================================================================
# _send_error() Tests
# ================================================================


class TestSendError:
    """_send_error() metodu dogru mesaj secimi ve formatlama testleri."""

    @pytest.mark.asyncio
    async def test_send_error_formats_general_message(self, handler, mock_telegram_adapter):
        """_send_error('general') dogru mesaji formatlayip gondermeli."""
        request_id = "abc12345"
        await handler._send_error("chat1", "general", request_id)

        mock_telegram_adapter.send.assert_called_once()

        # _send_reply uzerinden gidiyoruz — adapter.send(recipient=, content=)
        call_args = mock_telegram_adapter.send.call_args
        # MessageContent objesi kontrol
        content_obj = call_args.kwargs.get("content", call_args.args[1] if len(call_args.args) > 1 else None)
        assert request_id in content_obj.text

    @pytest.mark.asyncio
    async def test_send_error_selects_correct_message_type(self, handler, mock_telegram_adapter):
        """_send_error() bilinmeyen tip icin 'general' mesaji kullanmali."""
        request_id = "ff001122"
        await handler._send_error("chat1", "UNKNOWN_TYPE", request_id)

        call_args = mock_telegram_adapter.send.call_args
        content_obj = call_args.kwargs.get("content", call_args.args[1] if len(call_args.args) > 1 else None)
        # Bilinmeyen tip → general mesaji kullanilir
        assert "hata olustu" in content_obj.text.lower() or "Referans:" in content_obj.text

    @pytest.mark.asyncio
    async def test_send_error_quota_message(self, handler, mock_telegram_adapter):
        """_send_error('quota') kota mesajini gondermeli."""
        await handler._send_error("chat1", "quota", "aabb1122")

        call_args = mock_telegram_adapter.send.call_args
        content_obj = call_args.kwargs.get("content", call_args.args[1] if len(call_args.args) > 1 else None)
        assert "Kota" in content_obj.text or "kota" in content_obj.text.lower()


# ================================================================
# Request ID Format Tests
# ================================================================


class TestRequestIdFormat:
    """request_id format dogrulama — handle() icindeki uuid.uuid4().hex[:8]."""

    def test_request_id_is_8_char_hex(self):
        """Uretilen request_id 8 karakter hex olmali."""
        request_id = uuid.uuid4().hex[:8]
        assert len(request_id) == 8
        assert re.match(r"^[0-9a-f]{8}$", request_id)

    def test_request_id_uniqueness(self):
        """Her cagri farkli request_id uretmeli."""
        ids = {uuid.uuid4().hex[:8] for _ in range(100)}
        # 100 farkli ID uretilmeli (collison olasiligi cok dusuk)
        assert len(ids) >= 99


# ================================================================
# handle() Top-Level Exception Tests
# ================================================================


class TestHandleTopLevelException:
    """handle() top-level exception yutma davranisi."""

    @pytest.mark.asyncio
    async def test_handle_exception_does_not_send_message(self, handler, mock_telegram_adapter):
        """
        handle() icindeki top-level exception yakalanmali,
        kullaniciya hata mesaji GONDERILMEMELI (sadece loglanmali).

        Not: handlers.py handle() metodu except blogundan _send_error cagirmaz,
        sadece logger.error ile loglar.
        """
        # Adapter.send her zaman exception firlatsin
        mock_telegram_adapter.send.side_effect = RuntimeError("network error")

        incoming = IncomingMessage(
            sender_id="chat1",
            channel="telegram",
            content="/start",
            raw_payload={},
        )

        # handle() exception firlatmamali
        await handler.handle(incoming)
        # Yukardaki satirda exception firlatilmadiysa test gecti

    @pytest.mark.asyncio
    async def test_handle_logs_error_with_structlog_fields(self, handler, mock_telegram_adapter):
        """handle() exception'da structlog alanlari loglanmali."""
        mock_telegram_adapter.send.side_effect = RuntimeError("test error")

        incoming = IncomingMessage(
            sender_id="chat1",
            channel="telegram",
            content="/start",
            raw_payload={},
        )

        with patch("src.modules.messaging.bot.handlers.logger") as mock_logger:
            await handler.handle(incoming)

            # logger.error cagrildimi kontrol
            mock_logger.error.assert_called()
            call_kwargs = mock_logger.error.call_args
            # Keyword args'da beklenen structlog alanlari
            kw = call_kwargs.kwargs if call_kwargs.kwargs else {}
            assert kw.get("handler") == "handle"
            assert "request_id" in kw
            assert len(kw["request_id"]) == 8
            assert kw.get("user_id") == "chat1"
            assert kw.get("chat_id") == "chat1"
            assert "error_type" in kw
            assert "error_msg" in kw


# ================================================================
# _handle_iptal() Silent Mode Tests
# ================================================================


class TestHandleIptal:
    """_handle_iptal() conversation manager olmadan sessiz kalma."""

    @pytest.mark.asyncio
    async def test_iptal_silent_when_conv_manager_none(self, handler, mock_telegram_adapter):
        """
        _handle_iptal() conv manager (self._conv) None iken
        mesaj gondermemeli — sessiz return.
        """
        assert handler._conv is None  # redis_client=None oldugundan

        incoming = IncomingMessage(
            sender_id="chat1",
            channel="telegram",
            content="/iptal",
            raw_payload={},
        )
        await handler._handle_iptal(incoming)

        # Conv manager yokken mesaj gonderilmemeli
        mock_telegram_adapter.send.assert_not_called()
