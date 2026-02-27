"""
TASK-141: Unit Test Fixtures — DB/Redis/Telegram API bagimsiz

Bu conftest.py, pure unit testler icin mock fixture'lar saglar.
Ana conftest.py'deki DB-dependent fixture'lara ihtiyac duymaz.

Tum fixture'lar in-memory mock objeler kullanir:
    - mock_redis: In-memory dict tabanli Redis simulasyonu
    - mock_telegram_adapter: Telegram API mock
    - mock_session_factory: SQLAlchemy session factory mock
    - mock_telegram_update: IncomingMessage factory
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

# ================================================================
# Sabitler
# ================================================================

MATCH_ID_1 = uuid.UUID("c0000000-0000-0000-0000-000000000001")
BOT_CHAT_ID = "123456789"
BOT_TOKEN = "1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ"


# ================================================================
# Mock Redis
# ================================================================


@pytest.fixture
def mock_redis():
    """
    Mock async Redis client — conversation state testleri icin.

    get/set/delete/expire metodlari AsyncMock.
    In-memory dict ile basit key-value simulasyonu saglar.
    """
    redis = AsyncMock()
    store: dict[str, str] = {}

    async def _get(key: str) -> str | None:
        return store.get(key)

    async def _set(key: str, value: str, *, ex: int | None = None) -> None:
        store[key] = value

    async def _delete(key: str) -> None:
        store.pop(key, None)

    redis.get = AsyncMock(side_effect=_get)
    redis.set = AsyncMock(side_effect=_set)
    redis.delete = AsyncMock(side_effect=_delete)
    redis._store = store  # Test icinde dogrudan erisim
    return redis


# ================================================================
# Mock Telegram Adapter
# ================================================================


@pytest.fixture
def mock_telegram_adapter():
    """
    Mock TelegramAdapter — gercek Telegram API cagrisi yok.

    send() → basarili SendResult simulasyonu.
    answer_callback_query() → None.
    edit_message_text() → None.
    """
    adapter = AsyncMock()
    send_result = AsyncMock()
    send_result.success = True
    send_result.error = None
    adapter.send = AsyncMock(return_value=send_result)
    adapter.answer_callback_query = AsyncMock()
    adapter.edit_message_text = AsyncMock()
    return adapter


# ================================================================
# Mock Session Factory
# ================================================================


@pytest.fixture
def mock_session_factory():
    """
    Mock async_sessionmaker — DB bagimsiz test icin.

    session_factory() context manager olarak mock session dondurur.
    Pattern: async with session_factory() as db: ...
    Session: execute, scalar_one_or_none, commit, refresh, rollback.
    """
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=None)
    session.execute = AsyncMock(return_value=mock_result)

    # async with factory() as db: pattern'i icin
    # factory() → context_manager objesi dondurmeli
    # context_manager.__aenter__() → session
    # context_manager.__aexit__() → False
    ctx_manager = MagicMock()
    ctx_manager.__aenter__ = AsyncMock(return_value=session)
    ctx_manager.__aexit__ = AsyncMock(return_value=False)

    factory = MagicMock()
    factory.return_value = ctx_manager
    factory._mock_session = session  # Test icinde dogrudan erisim
    factory._mock_result = mock_result
    return factory


# ================================================================
# Mock IncomingMessage Factory
# ================================================================


@pytest.fixture
def mock_telegram_update():
    """
    Mock IncomingMessage factory — farkli senaryo testleri icin.

    Kullanim:
        msg = mock_telegram_update(content="/start")
        msg = mock_telegram_update(content="match:uuid:accept", is_callback=True)
    """

    def _create(
        content: str = "",
        sender_id: str = BOT_CHAT_ID,
        channel: str = "telegram",
        media_url: str | None = None,
        raw_payload: dict | None = None,
    ):
        msg = MagicMock()
        msg.sender_id = sender_id
        msg.channel = channel
        msg.content = content
        msg.media_url = media_url
        msg.raw_payload = raw_payload or {}
        return msg

    return _create
