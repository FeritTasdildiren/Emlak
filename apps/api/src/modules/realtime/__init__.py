"""
Emlak Teknoloji Platformu - Realtime Module

WebSocket tabanli gercek zamanli iletisim altyapisi.

Durum: STUB — temel altyapi hazir, varsayilan KAPALI.
Gelecekte genisletilecek alanlar:
    - Redis PubSub ile coklu worker senkronizasyonu
    - Canli mesajlasma (bidirectional)
    - Eslesme alert'leri
"""

from src.modules.realtime.events import EventType, WebSocketEvent
from src.modules.realtime.websocket_manager import ConnectionManager

__all__ = [
    "ConnectionManager",
    "EventType",
    "WebSocketEvent",
]
