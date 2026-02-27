"""
TASK-141: Conversation State Manager Unit Tests

ConversationStateManager ve ilgili siniflarin pure unit testleri.
Redis bagimsiz — mock Redis client kullanilir.

Kapsam:
    - WizardStep enum degerleri ve akisi
    - ConversationState serialize/deserialize (JSON round-trip)
    - ConversationStateManager CRUD islemleri (get/start/advance/clear)
    - TTL dogrulama (30 dakika = 1800 saniye)
    - Key isolation (conv:{user_id})
    - Expire sonrasi None donusu (IDLE simulasyonu)
    - increment_retries ve max retry kontrolu
    - is_active kontrolu (IDLE/DONE vs aktif adimlar)
"""

from __future__ import annotations

import json

import pytest

from src.modules.messaging.bot.conversation_state import (
    _CONV_REDIS_PREFIX,
    _CONV_TTL_SECONDS,
    ConversationState,
    ConversationStateManager,
    WizardStep,
)

# ================================================================
# WizardStep Enum Tests
# ================================================================


class TestWizardStep:
    """WizardStep enum degerleri ve sirasi."""

    def test_all_steps_defined(self):
        """WizardStep 6 adim icermeli."""
        expected = {"IDLE", "PHOTO", "LOCATION", "DETAILS", "CONFIRM", "DONE"}
        actual = {step.value for step in WizardStep}
        assert actual == expected

    def test_step_values_are_strings(self):
        """WizardStep StrEnum — her deger kendi adiyla esit olmali."""
        for step in WizardStep:
            assert step.value == step.name

    def test_step_ordering_matches_flow(self):
        """Wizard akisi: IDLE → PHOTO → LOCATION → DETAILS → CONFIRM → DONE."""
        flow = [
            WizardStep.IDLE,
            WizardStep.PHOTO,
            WizardStep.LOCATION,
            WizardStep.DETAILS,
            WizardStep.CONFIRM,
            WizardStep.DONE,
        ]
        assert len(flow) == 6
        # StrEnum sirasi tanimlanma sirasina goredir
        assert list(WizardStep) == flow


# ================================================================
# ConversationState Serialize/Deserialize Tests
# ================================================================


class TestConversationStateSerialization:
    """ConversationState JSON serialize/deserialize round-trip testleri."""

    def test_to_json_produces_valid_json(self):
        """to_json() gecerli JSON string dondurmeli."""
        state = ConversationState(
            step=WizardStep.PHOTO,
            data={"photo_url": "https://example.com/img.jpg"},
            retries=1,
            created_at=1000.0,
            updated_at=2000.0,
        )
        raw = state.to_json()
        parsed = json.loads(raw)

        assert parsed["step"] == "PHOTO"
        assert parsed["data"]["photo_url"] == "https://example.com/img.jpg"
        assert parsed["retries"] == 1
        assert parsed["created_at"] == 1000.0
        assert parsed["updated_at"] == 2000.0

    def test_from_json_restores_state(self):
        """from_json() JSON string'den ConversationState olusturmali."""
        raw = json.dumps({
            "step": "LOCATION",
            "data": {"district": "Kadikoy"},
            "retries": 2,
            "created_at": 1000.0,
            "updated_at": 2000.0,
        })
        state = ConversationState.from_json(raw)

        assert state.step == WizardStep.LOCATION
        assert state.data == {"district": "Kadikoy"}
        assert state.retries == 2

    def test_round_trip_preserves_data(self):
        """to_json() → from_json() veri kaybina yol acmamali."""
        original = ConversationState(
            step=WizardStep.DETAILS,
            data={"rooms": "3+1", "net_area": 120},
            retries=0,
            created_at=1700000000.0,
            updated_at=1700000100.0,
        )
        restored = ConversationState.from_json(original.to_json())

        assert restored.step == original.step
        assert restored.data == original.data
        assert restored.retries == original.retries
        assert restored.created_at == original.created_at
        assert restored.updated_at == original.updated_at

    def test_default_state_is_idle(self):
        """Varsayilan ConversationState IDLE adiminda olmali."""
        state = ConversationState()
        assert state.step == WizardStep.IDLE
        assert state.data == {}
        assert state.retries == 0


# ================================================================
# ConversationStateManager Tests
# ================================================================


class TestConversationStateManager:
    """ConversationStateManager CRUD islemleri — mock Redis ile."""

    @pytest.fixture
    def manager(self, mock_redis):
        """ConversationStateManager instance — mock Redis ile."""
        return ConversationStateManager(mock_redis)

    # --- Key Format ---

    def test_key_format_uses_prefix(self, manager):
        """Redis key 'conv:{user_id}' formatinda olmali."""
        key = manager._key("12345")
        assert key == f"{_CONV_REDIS_PREFIX}12345"
        assert key == "conv:12345"

    def test_key_isolation_per_user(self, manager):
        """Farkli user_id'ler farkli key'ler olusturmali."""
        assert manager._key("111") != manager._key("222")

    # --- start() ---

    @pytest.mark.asyncio
    async def test_start_creates_photo_step(self, manager, mock_redis):
        """start() PHOTO adiminda yeni state olusturmali."""
        state = await manager.start("user1")

        assert state.step == WizardStep.PHOTO
        assert state.data == {}
        assert state.retries == 0
        assert state.created_at > 0
        assert state.updated_at > 0

    @pytest.mark.asyncio
    async def test_start_sets_ttl(self, manager, mock_redis):
        """start() Redis'e 1800 saniye TTL ile yazmali."""
        await manager.start("user1")

        mock_redis.set.assert_called_once()
        call_kwargs = mock_redis.set.call_args
        assert call_kwargs.kwargs.get("ex") == _CONV_TTL_SECONDS

    # --- get() ---

    @pytest.mark.asyncio
    async def test_get_returns_none_when_not_exists(self, manager, mock_redis):
        """get() state yoksa None dondurmeli."""
        result = await manager.get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_returns_state_after_start(self, manager, mock_redis):
        """get() start() sonrasi state dondurmeli."""
        await manager.start("user1")
        state = await manager.get("user1")

        assert state is not None
        assert state.step == WizardStep.PHOTO

    # --- advance() ---

    @pytest.mark.asyncio
    async def test_advance_changes_step(self, manager, mock_redis):
        """advance() adimi degistirmeli."""
        await manager.start("user1")
        updated = await manager.advance("user1", WizardStep.LOCATION, {"photo_url": "test.jpg"})

        assert updated is not None
        assert updated.step == WizardStep.LOCATION
        assert updated.data["photo_url"] == "test.jpg"

    @pytest.mark.asyncio
    async def test_advance_merges_data(self, manager, mock_redis):
        """advance() mevcut data'yi korumali ve yeni veri ile merge etmeli."""
        await manager.start("user1")
        await manager.advance("user1", WizardStep.LOCATION, {"photo_url": "img.jpg"})
        updated = await manager.advance(
            "user1",
            WizardStep.DETAILS,
            {"district": "Kadikoy"},
        )

        assert updated is not None
        assert updated.data["photo_url"] == "img.jpg"
        assert updated.data["district"] == "Kadikoy"

    @pytest.mark.asyncio
    async def test_advance_returns_none_when_no_state(self, manager, mock_redis):
        """advance() state yoksa None dondurmeli."""
        result = await manager.advance("no_user", WizardStep.LOCATION)
        assert result is None

    @pytest.mark.asyncio
    async def test_advance_resets_retries_by_default(self, manager, mock_redis):
        """advance() varsayilan olarak retries sifirlamali."""
        await manager.start("user1")
        await manager.increment_retries("user1")
        updated = await manager.advance("user1", WizardStep.LOCATION)

        assert updated is not None
        assert updated.retries == 0

    @pytest.mark.asyncio
    async def test_advance_preserves_retries_when_flag_false(self, manager, mock_redis):
        """advance(reset_retries=False) retries'i korumali."""
        await manager.start("user1")
        await manager.increment_retries("user1")
        updated = await manager.advance(
            "user1",
            WizardStep.LOCATION,
            reset_retries=False,
        )

        assert updated is not None
        assert updated.retries == 1

    # --- clear() ---

    @pytest.mark.asyncio
    async def test_clear_removes_state(self, manager, mock_redis):
        """clear() sonrasi get() None dondurmeli."""
        await manager.start("user1")
        await manager.clear("user1")
        result = await manager.get("user1")

        assert result is None

    # --- increment_retries() ---

    @pytest.mark.asyncio
    async def test_increment_retries_increases_count(self, manager, mock_redis):
        """increment_retries() sayaci 1 arttirmali."""
        await manager.start("user1")
        count = await manager.increment_retries("user1")
        assert count == 1

        count = await manager.increment_retries("user1")
        assert count == 2

    @pytest.mark.asyncio
    async def test_increment_retries_returns_zero_when_no_state(self, manager, mock_redis):
        """increment_retries() state yoksa 0 dondurmeli."""
        count = await manager.increment_retries("nonexistent")
        assert count == 0

    # --- is_active() ---

    @pytest.mark.asyncio
    async def test_is_active_true_for_photo_step(self, manager, mock_redis):
        """is_active() PHOTO adiminda True dondurmeli."""
        await manager.start("user1")
        assert await manager.is_active("user1") is True

    @pytest.mark.asyncio
    async def test_is_active_false_for_no_state(self, manager, mock_redis):
        """is_active() state yoksa False dondurmeli."""
        assert await manager.is_active("nonexistent") is False

    @pytest.mark.asyncio
    async def test_is_active_false_for_done_step(self, manager, mock_redis):
        """is_active() DONE adiminda False dondurmeli."""
        await manager.start("user1")
        await manager.advance("user1", WizardStep.DONE)
        assert await manager.is_active("user1") is False

    @pytest.mark.asyncio
    async def test_is_active_false_for_idle_step(self, manager, mock_redis):
        """is_active() IDLE adiminda False dondurmeli."""
        # Manually set an IDLE state
        state = ConversationState(step=WizardStep.IDLE)
        mock_redis._store["conv:user1"] = state.to_json()
        assert await manager.is_active("user1") is False

    # --- TTL ---

    @pytest.mark.asyncio
    async def test_ttl_value_is_1800_seconds(self):
        """TTL sabiti 1800 saniye (30 dakika) olmali."""
        assert _CONV_TTL_SECONDS == 1800

    @pytest.mark.asyncio
    async def test_advance_refreshes_ttl(self, manager, mock_redis):
        """advance() her cagride TTL'i yenilemeli."""
        await manager.start("user1")
        mock_redis.set.reset_mock()

        await manager.advance("user1", WizardStep.LOCATION)

        mock_redis.set.assert_called_once()
        call_kwargs = mock_redis.set.call_args
        assert call_kwargs.kwargs.get("ex") == _CONV_TTL_SECONDS
