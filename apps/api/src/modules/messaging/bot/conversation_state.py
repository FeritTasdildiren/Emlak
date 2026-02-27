"""
Emlak Teknoloji Platformu - Conversation State Manager

Redis tabanli konusma durumu yonetimi.
Telegram bot ilan olusturma wizard'i icin multi-step state yonetir.

State akisi:
    IDLE → PHOTO → LOCATION → DETAILS → CONFIRM → DONE

Kullanim:
    state_mgr = ConversationStateManager(redis_client)
    await state_mgr.start(user_id)
    state = await state_mgr.get(user_id)
    await state_mgr.advance(user_id, "LOCATION", {"photo_url": "..."})
    await state_mgr.clear(user_id)

Redis key pattern: conv:{user_id}
TTL: 30 dakika (her guncelleme ile yenilenir)

Referans: TASK-134
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    import redis.asyncio as aioredis

# ================================================================
# Sabitler
# ================================================================

_CONV_REDIS_PREFIX = "conv:"
_CONV_TTL_SECONDS = 1800  # 30 dakika
_MAX_RETRIES = 3  # Detay girisi maksimum deneme


# ================================================================
# Step Enum
# ================================================================


class WizardStep(StrEnum):
    """Ilan wizard adim tanimlari."""

    IDLE = "IDLE"
    PHOTO = "PHOTO"
    LOCATION = "LOCATION"
    DETAILS = "DETAILS"
    CONFIRM = "CONFIRM"
    DONE = "DONE"


# ================================================================
# ConversationState
# ================================================================


@dataclass
class ConversationState:
    """
    Kullanici bazli konusma durumu.

    Attributes:
        step: Mevcut wizard adimi.
        data: Adimlar boyunca biriken veri (photo_url, district, vb.).
        retries: Detay girisi deneme sayaci.
        created_at: State olusturulma zamani (Unix timestamp).
        updated_at: Son guncelleme zamani (Unix timestamp).
    """

    step: WizardStep = WizardStep.IDLE
    data: dict[str, Any] = field(default_factory=dict)
    retries: int = 0
    created_at: float = 0.0
    updated_at: float = 0.0

    def to_json(self) -> str:
        """State'i JSON string'e serialize eder."""
        return json.dumps(
            {
                "step": self.step.value,
                "data": self.data,
                "retries": self.retries,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
        )

    @classmethod
    def from_json(cls, raw: str) -> ConversationState:
        """JSON string'den ConversationState olusturur."""
        payload = json.loads(raw)
        return cls(
            step=WizardStep(payload["step"]),
            data=payload.get("data", {}),
            retries=payload.get("retries", 0),
            created_at=payload.get("created_at", 0.0),
            updated_at=payload.get("updated_at", 0.0),
        )


# ================================================================
# ConversationStateManager
# ================================================================


class ConversationStateManager:
    """
    Redis uzerinden conversation state CRUD islemleri.

    Her islem sonrasi TTL 30dk olarak yenilenir.

    Args:
        redis_client: Async Redis client instance.
    """

    def __init__(self, redis_client: aioredis.Redis) -> None:
        self._redis = redis_client

    def _key(self, user_id: str) -> str:
        """Redis key olusturur."""
        return f"{_CONV_REDIS_PREFIX}{user_id}"

    async def get(self, user_id: str) -> ConversationState | None:
        """
        Kullanicinin mevcut conversation state'ini dondurur.

        Args:
            user_id: Telegram chat ID.

        Returns:
            ConversationState veya None (yoksa/expire olduysa).
        """
        raw: str | None = await self._redis.get(self._key(user_id))
        if raw is None:
            return None
        return ConversationState.from_json(raw)

    async def start(self, user_id: str) -> ConversationState:
        """
        Yeni wizard baslatir (PHOTO adimi).

        Mevcut state varsa uzerine yazar.

        Args:
            user_id: Telegram chat ID.

        Returns:
            Yeni olusturulan ConversationState.
        """
        now = time.time()
        state = ConversationState(
            step=WizardStep.PHOTO,
            data={},
            retries=0,
            created_at=now,
            updated_at=now,
        )
        await self._redis.set(
            self._key(user_id),
            state.to_json(),
            ex=_CONV_TTL_SECONDS,
        )
        return state

    async def advance(
        self,
        user_id: str,
        next_step: WizardStep,
        new_data: dict[str, Any] | None = None,
        *,
        reset_retries: bool = True,
    ) -> ConversationState | None:
        """
        Konusmay bir sonraki adima ilerletir.

        Mevcut data'yi korur, new_data ile merge eder.

        Args:
            user_id: Telegram chat ID.
            next_step: Gecilecek yeni adim.
            new_data: Adima ait yeni veri (merge edilir).
            reset_retries: True ise retry sayaci sifirlanir.

        Returns:
            Guncellenmis ConversationState veya None (state yoksa).
        """
        state = await self.get(user_id)
        if state is None:
            return None

        state.step = next_step
        if new_data:
            state.data.update(new_data)
        if reset_retries:
            state.retries = 0
        state.updated_at = time.time()

        await self._redis.set(
            self._key(user_id),
            state.to_json(),
            ex=_CONV_TTL_SECONDS,
        )
        return state

    async def increment_retries(self, user_id: str) -> int:
        """
        Retry sayacini 1 arttirir.

        Args:
            user_id: Telegram chat ID.

        Returns:
            Guncel retry sayisi. State yoksa 0.
        """
        state = await self.get(user_id)
        if state is None:
            return 0

        state.retries += 1
        state.updated_at = time.time()

        await self._redis.set(
            self._key(user_id),
            state.to_json(),
            ex=_CONV_TTL_SECONDS,
        )
        return state.retries

    async def clear(self, user_id: str) -> None:
        """
        Conversation state'i temizler (wizard iptal/tamamlama).

        Args:
            user_id: Telegram chat ID.
        """
        await self._redis.delete(self._key(user_id))

    async def is_active(self, user_id: str) -> bool:
        """
        Kullanicinin aktif wizard'i var mi kontrol eder.

        Args:
            user_id: Telegram chat ID.

        Returns:
            True ise aktif wizard var.
        """
        state = await self.get(user_id)
        return state is not None and state.step not in (
            WizardStep.IDLE,
            WizardStep.DONE,
        )
