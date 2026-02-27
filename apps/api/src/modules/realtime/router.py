"""
Emlak Teknoloji Platformu - WebSocket Router

WebSocket endpoint: ws://host/ws?token=<JWT>

Akis:
    1. Query param'dan JWT token al
    2. Token'i decode et (dogrulama + user_id cikarma)
    3. ConnectionManager'a baglan
    4. Heartbeat ping-pong destegi
    5. Basit echo (stub) — gelecekte event dispatch'e donusecek

Guvenlik:
    - WebSocket baglantisi JWT ile dogrulanir
    - Token gecersiz ise baglanti REDDEDILIR (4401 close code)
    - Blacklist kontrolu YAPILMAZ (stub) — gelecekte eklenecek

Public Path Notu:
    - /ws endpoint'i TenantMiddleware'den muaf tutulmalidir
      (WebSocket upgrade HTTP middleware chain'i atlar)
    - JWT dogrulama bu router icinde yapilir

Heartbeat:
    - Client "ping" text mesaji gonderdikçe server "pong" ile yanit verir
    - Baglanti saglik kontrolu icin kullanilir

Durum: STUB — echo + heartbeat, ileriki sprintlerde event dispatch eklenecek.
"""

from __future__ import annotations

import structlog
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from jose import JWTError, jwt
from starlette.websockets import WebSocketState

from src.config import settings
from src.modules.realtime.events import EventType, WebSocketEvent
from src.modules.realtime.websocket_manager import ConnectionManager

logger = structlog.get_logger(__name__)

router = APIRouter(tags=["websocket"])

# Singleton manager — lifespan'da app.state'e de atanacak
manager = ConnectionManager()


def _authenticate_token(token: str) -> dict | None:
    """
    JWT token'i dogrular ve payload'u dondurur.

    WebSocket icin sadece token decode yapilir.
    Blacklist kontrolu, DB user lookup gibi agir islemler
    stub asamasinda yapilmiyor — gelecekte eklenecek.

    Args:
        token: JWT access token.

    Returns:
        JWT payload dict veya None (gecersiz token).
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )

        # Token tipi kontrolu
        if payload.get("type") != "access":
            return None

        # user_id (sub) kontrolu
        if not payload.get("sub"):
            return None

        return payload
    except JWTError:
        return None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str | None = None) -> None:
    """
    WebSocket baglanti endpoint'i.

    Kullanim:
        ws://host/ws?token=<JWT_ACCESS_TOKEN>

    Mesaj protokolu (stub):
        Client → Server:
            - "ping"       → Server "pong" ile yanit verir (heartbeat)
            - herhangi JSON → Server echo olarak geri gonderir

        Server → Client:
            - WebSocketEvent formati: {"type": "...", "payload": {...}, "timestamp": "..."}

    Close Codes:
        - 4401: JWT token eksik veya gecersiz
        - 1000: Normal kapanis
        - 1011: Server hatasi
    """
    # --- JWT dogrulama ---
    if not token:
        await websocket.close(code=4401, reason="Token gerekli")
        return

    payload = _authenticate_token(token)
    if payload is None:
        await websocket.close(code=4401, reason="Gecersiz veya suresi dolmus token")
        return

    user_id: str = payload["sub"]

    # --- Baglanti kabul ---
    await manager.connect(user_id, websocket)

    # Hosgeldin mesaji gonder
    welcome_event = WebSocketEvent(
        type=EventType.SYSTEM,
        payload={
            "message": "WebSocket baglantisi basarili",
            "user_id": user_id,
        },
    )
    try:
        await websocket.send_json(welcome_event.to_dict())
    except Exception:
        manager.disconnect(user_id, websocket)
        return

    # --- Mesaj dongusu ---
    try:
        while True:
            data = await websocket.receive_text()

            # Heartbeat: ping → pong
            if data.strip().lower() == "ping":
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text("pong")
                continue

            # Stub: Echo — gelen mesaji geri gonder
            echo_event = WebSocketEvent(
                type=EventType.SYSTEM,
                payload={"echo": data},
            )
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_json(echo_event.to_dict())

    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
        logger.info("ws_client_disconnected", user_id=user_id)
    except Exception as exc:
        logger.error(
            "ws_unexpected_error",
            user_id=user_id,
            error=str(exc),
            exc_info=True,
        )
        manager.disconnect(user_id, websocket)
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.close(code=1011, reason="Sunucu hatasi")
        except Exception:
            pass  # Baglanti zaten kopmus olabilir
