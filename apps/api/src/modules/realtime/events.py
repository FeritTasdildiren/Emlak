"""
Emlak Teknoloji Platformu - WebSocket Event Definitions

WebSocket uzerinden iletilen event tipleri ve veri yapilari.

EventType enum'u frontend ile senkron tutulmalidir:
    Frontend karsiligi: apps/web/src/types/websocket.ts

Kullanim:
    event = WebSocketEvent(
        type=EventType.NOTIFICATION,
        payload={"title": "Yeni eslesme", "body": "..."},
    )
    await manager.send_personal(user_id, event.to_dict())
"""

from __future__ import annotations

import enum
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any


class EventType(enum.StrEnum):
    """
    WebSocket event tipleri.

    Backend ve frontend ayni enum degerlerini kullanir.
    Yeni tip eklerken frontend types/websocket.ts dosyasini da guncelle.
    """

    NOTIFICATION = "notification"
    MATCH_UPDATE = "match_update"
    VALUATION_COMPLETE = "valuation_complete"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class WebSocketEvent:
    """
    WebSocket uzerinden iletilen event veri yapisi.

    Immutable (frozen) — olusturulduktan sonra degistirilemez.
    slots=True ile bellek optimizasyonu yapilir.

    Attributes:
        type: Event tipi (EventType enum).
        payload: Event verisi (serbest yapida dict).
        timestamp: Event olusturulma zamani (ISO 8601, UTC).

    Kullanim:
        event = WebSocketEvent(
            type=EventType.NOTIFICATION,
            payload={"title": "Yeni bildirim"},
        )
        json_data = event.to_dict()
    """

    type: EventType
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """
        Event'i JSON-serializable dict'e donusturur.

        EventType enum'u str degerine cevrilir (frontend uyumlulugu).
        """
        data = asdict(self)
        data["type"] = self.type.value
        return data
