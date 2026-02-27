"""
Emlak Teknoloji Platformu - WebSocket Event Emitter

Uygulama katmanindan WebSocket event'lerini gondermek icin yardimci fonksiyonlar.

Temel prensip: GRACEFUL DEGRADATION
    - Kullanici bagli degilse sessizce gec (fire-and-forget)
    - WebSocket hatasi uygulama akisini KESMEZ
    - Hata loglama yapilir ama exception yukariya firlatilmaz

Kullanim:
    from src.modules.realtime.event_emitter import emit_event

    # Bildirim olusturulunca:
    await emit_event(
        user_id=str(user.id),
        event_type=EventType.NOTIFICATION,
        payload={"title": "Yeni eslesme", "notification_id": str(notif.id)},
    )

    # Degerleme tamamlaninca:
    await emit_event(
        user_id=str(user.id),
        event_type=EventType.VALUATION_COMPLETE,
        payload={"valuation_id": str(val.id), "estimated_price": 3_500_000},
    )

Gelecek genisleme:
    - Redis PubSub ile coklu worker'a event yayma
    - Event batching (yuksek hacimli senaryolar)
    - Event persistence (offline kullanicilar icin kuyruk)
"""

from __future__ import annotations

from typing import Any

import structlog

from src.modules.realtime.events import EventType, WebSocketEvent

logger = structlog.get_logger(__name__)

# Lazy import — circular import onleme
# manager, router modulu yuklendiginde olusturulur
_manager = None


def _get_manager():
    """
    ConnectionManager singleton'ini lazy olarak yukler.

    Circular import'u onlemek icin ilk kullanimda import edilir.
    manager bulunamazsa None doner (WebSocket devre disi).
    """
    global _manager
    if _manager is None:
        try:
            from src.modules.realtime.router import manager

            _manager = manager
        except ImportError:
            logger.warning("ws_manager_import_failed")
            return None
    return _manager


async def emit_event(
    user_id: str,
    event_type: EventType,
    payload: dict[str, Any] | None = None,
) -> bool:
    """
    Belirli bir kullaniciya WebSocket event'i gonderir.

    Graceful degradation: baglanti yoksa veya hata olursa sessizce gecer.
    Bu fonksiyon ASLA exception firlatmaz.

    Args:
        user_id: Hedef kullanici UUID (str).
        event_type: Event tipi (EventType enum).
        payload: Event verisi (opsiyonel).

    Returns:
        True: En az bir baglantiya basariyla gonderildi.
        False: Kullanici bagli degil veya hata olustu.
    """
    try:
        mgr = _get_manager()
        if mgr is None:
            return False

        if not mgr.is_connected(user_id):
            return False

        event = WebSocketEvent(
            type=event_type,
            payload=payload or {},
        )

        sent = await mgr.send_personal(user_id, event.to_dict())

        if sent > 0:
            logger.debug(
                "ws_event_emitted",
                user_id=user_id,
                event_type=event_type.value,
                sent_count=sent,
            )

        return sent > 0

    except Exception as exc:
        # KRITIK: Bu fonksiyon ASLA uygulama akisini kesmez
        logger.error(
            "ws_event_emit_failed",
            user_id=user_id,
            event_type=event_type.value,
            error=str(exc),
        )
        return False


async def broadcast_event(
    event_type: EventType,
    payload: dict[str, Any] | None = None,
) -> int:
    """
    Tum bagli kullanicilara WebSocket event'i gonderir.

    Kullanim: Sistem bakimi, global duyuru vb.

    Args:
        event_type: Event tipi (EventType enum).
        payload: Event verisi (opsiyonel).

    Returns:
        Basarili gonderim sayisi. Hata durumunda 0.
    """
    try:
        mgr = _get_manager()
        if mgr is None:
            return 0

        event = WebSocketEvent(
            type=event_type,
            payload=payload or {},
        )

        sent = await mgr.broadcast(event.to_dict())

        if sent > 0:
            logger.info(
                "ws_event_broadcast",
                event_type=event_type.value,
                sent_count=sent,
            )

        return sent

    except Exception as exc:
        logger.error(
            "ws_event_broadcast_failed",
            event_type=event_type.value,
            error=str(exc),
        )
        return 0
