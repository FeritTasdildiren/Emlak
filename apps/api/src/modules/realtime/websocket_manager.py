"""
Emlak Teknoloji Platformu - WebSocket Connection Manager

Aktif WebSocket baglantilarini yonetir: connect, disconnect, mesaj gonderme.

Durum: STUB — tek process, in-memory dict.
Gelecek genisleme:
    - Redis PubSub ile coklu worker senkronizasyonu
    - Connection pooling
    - Heartbeat monitoring (stale connection temizleme)

Kullanim:
    manager = ConnectionManager()

    # Baglanti
    await manager.connect(user_id, websocket)

    # Kisisel mesaj
    await manager.send_personal(user_id, {"type": "notification", ...})

    # Broadcast
    await manager.broadcast({"type": "system", "payload": {"message": "Bakım var"}})

    # Baglanti kesme
    manager.disconnect(user_id, websocket)

Thread Safety:
    FastAPI WebSocket handler'lari asyncio event loop'ta calisir.
    dict islemleri GIL tarafindan korunur — ek lock gereksiz (tek process).
    Coklu worker senaryosunda Redis PubSub'a gecirilecek.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from fastapi import WebSocket

logger = structlog.get_logger(__name__)


class ConnectionManager:
    """
    WebSocket baglanti yoneticisi.

    Her kullanici birden fazla baglantiya sahip olabilir (multi-tab/device).
    Baglantilar user_id bazinda gruplandiriliyor.

    Attributes:
        active_connections: user_id → [WebSocket, ...] eslesmesi.
    """

    def __init__(self) -> None:
        self.active_connections: dict[str, list[WebSocket]] = {}

    @property
    def total_connections(self) -> int:
        """Toplam aktif baglanti sayisi."""
        return sum(len(conns) for conns in self.active_connections.values())

    @property
    def connected_users(self) -> int:
        """Bagli kullanici sayisi (unique)."""
        return len(self.active_connections)

    async def connect(self, user_id: str, websocket: WebSocket) -> None:
        """
        WebSocket baglantisinini kabul eder ve aktif listesine ekler.

        Args:
            user_id: Kullanici UUID (str).
            websocket: FastAPI WebSocket instance.
        """
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

        logger.info(
            "ws_connected",
            user_id=user_id,
            total_connections=self.total_connections,
            connected_users=self.connected_users,
        )

    def disconnect(self, user_id: str, websocket: WebSocket) -> None:
        """
        WebSocket baglantisinini aktif listesinden cikarir.

        Kullanicinin son baglantisi ise user_id key'i de silinir.

        Args:
            user_id: Kullanici UUID (str).
            websocket: Kapatilan WebSocket instance.
        """
        connections = self.active_connections.get(user_id)
        if connections is None:
            return

        with contextlib.suppress(ValueError):
            connections.remove(websocket)

        if not connections:
            del self.active_connections[user_id]

        logger.info(
            "ws_disconnected",
            user_id=user_id,
            total_connections=self.total_connections,
            connected_users=self.connected_users,
        )

    async def send_personal(self, user_id: str, data: dict[str, Any]) -> int:
        """
        Belirli bir kullanicinin TUM baglantilarina mesaj gonderir.

        Bozuk baglantilari otomatik temizler (stale connection handling).

        Args:
            user_id: Hedef kullanici UUID (str).
            data: JSON-serializable mesaj verisi.

        Returns:
            Basarili gonderim sayisi.
        """
        connections = self.active_connections.get(user_id)
        if not connections:
            return 0

        sent = 0
        stale: list[WebSocket] = []

        for ws in connections:
            try:
                await ws.send_json(data)
                sent += 1
            except Exception:
                # Baglanti kopuk — temizlenecek
                stale.append(ws)
                logger.warning(
                    "ws_send_failed_stale",
                    user_id=user_id,
                )

        # Bozuk baglantilari temizle
        for ws in stale:
            self.disconnect(user_id, ws)

        return sent

    async def broadcast(self, data: dict[str, Any]) -> int:
        """
        Tum bagli kullanicilara mesaj gonderir.

        Args:
            data: JSON-serializable mesaj verisi.

        Returns:
            Basarili gonderim sayisi (toplam baglanti bazinda).
        """
        total_sent = 0

        # Iteration sirasinda dict degisebilir — snapshot al
        user_ids = list(self.active_connections.keys())

        for user_id in user_ids:
            sent = await self.send_personal(user_id, data)
            total_sent += sent

        if total_sent > 0:
            logger.info(
                "ws_broadcast",
                total_sent=total_sent,
                total_users=len(user_ids),
            )

        return total_sent

    def is_connected(self, user_id: str) -> bool:
        """Kullanicinin aktif baglantisi var mi?"""
        connections = self.active_connections.get(user_id)
        return bool(connections)
