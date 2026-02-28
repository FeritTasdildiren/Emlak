/**
 * Emlak Teknoloji Platformu - useWebSocket Hook
 *
 * WebSocket bağlantı yönetimi hook'u.
 *
 * Özellikler:
 *   - JWT token ile auth (localStorage'dan alınır)
 *   - Auto-reconnect (exponential backoff)
 *   - Connection state tracking
 *   - Heartbeat ping-pong
 *   - NEXT_PUBLIC_WS_ENABLED=false iken tamamen devre dışı
 *
 * Kullanım:
 *   const { connectionState, lastEvent, isConnected } = useWebSocket({
 *     onEvent: (event) => console.log("Event:", event),
 *   });
 *
 * Durum: STUB — temel altyapı, genişletmeye hazır.
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ConnectionState,
  type UseWebSocketReturn,
  type WebSocketEvent,
} from "@/types/websocket";

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------

const WS_ENABLED = process.env.NEXT_PUBLIC_WS_ENABLED === "true";

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL ||
  (typeof window !== "undefined"
    ? `${window.location.protocol === "https:" ? "wss:" : "ws:"}//${window.location.host}`
    : "ws://localhost:8000");

/** Heartbeat interval (ms) — server'a ping gönderme sıklığı */
const HEARTBEAT_INTERVAL_MS = 30_000;

/** Reconnect backoff parametreleri */
const RECONNECT_BASE_DELAY_MS = 1_000;
const RECONNECT_MAX_DELAY_MS = 30_000;
const RECONNECT_MAX_ATTEMPTS = 10;

// ---------------------------------------------------------------------------
// Hook Options
// ---------------------------------------------------------------------------

export interface UseWebSocketOptions {
  /** Her event geldiğinde çağrılır */
  onEvent?: (event: WebSocketEvent) => void;
  /** Bağlantı durumu değiştiğinde çağrılır */
  onConnectionChange?: (state: ConnectionState) => void;
  /** Hook'u devre dışı bırak (WS_ENABLED'dan bağımsız) */
  enabled?: boolean;
}

// ---------------------------------------------------------------------------
// Hook Implementation
// ---------------------------------------------------------------------------

export function useWebSocket(
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const { onEvent, onConnectionChange, enabled = true } = options;

  const [connectionState, setConnectionState] = useState<ConnectionState>(
    ConnectionState.DISCONNECTED
  );
  const [lastEvent, setLastEvent] = useState<WebSocketEvent | null>(null);

  // Refs — re-render tetiklemeden değişen değerler
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(
    null
  );
  const reconnectAttemptRef = useRef(0);
  const intentionalCloseRef = useRef(false);

  // Callback refs — stale closure önleme
  const onEventRef = useRef(onEvent);
  const onConnectionChangeRef = useRef(onConnectionChange);
  onEventRef.current = onEvent;
  onConnectionChangeRef.current = onConnectionChange;

  // ---------------------------------------------------------------------------
  // State Update Helper
  // ---------------------------------------------------------------------------

  const updateState = useCallback((state: ConnectionState) => {
    setConnectionState(state);
    onConnectionChangeRef.current?.(state);
  }, []);

  // ---------------------------------------------------------------------------
  // Heartbeat
  // ---------------------------------------------------------------------------

  const startHeartbeat = useCallback(() => {
    stopHeartbeat();
    heartbeatRef.current = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send("ping");
      }
    }, HEARTBEAT_INTERVAL_MS);
  }, []);

  const stopHeartbeat = useCallback(() => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
      heartbeatRef.current = null;
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Reconnect Logic (Exponential Backoff)
  // ---------------------------------------------------------------------------

  const scheduleReconnect = useCallback(() => {
    if (intentionalCloseRef.current) return;
    if (reconnectAttemptRef.current >= RECONNECT_MAX_ATTEMPTS) {
      updateState(ConnectionState.FAILED);
      return;
    }

    updateState(ConnectionState.RECONNECTING);

    const delay = Math.min(
      RECONNECT_BASE_DELAY_MS * Math.pow(2, reconnectAttemptRef.current),
      RECONNECT_MAX_DELAY_MS
    );

    reconnectTimeoutRef.current = setTimeout(() => {
      reconnectAttemptRef.current += 1;
      connect(); // eslint-disable-line @typescript-eslint/no-use-before-define
    }, delay);
  }, [updateState]); // eslint-disable-line react-hooks/exhaustive-deps

  // ---------------------------------------------------------------------------
  // Connect
  // ---------------------------------------------------------------------------

  const connect = useCallback(() => {
    // Önceki bağlantıyı temizle
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    const token =
      typeof window !== "undefined" ? localStorage.getItem("token") : null;
    if (!token) {
      updateState(ConnectionState.DISCONNECTED);
      return;
    }

    updateState(ConnectionState.CONNECTING);
    intentionalCloseRef.current = false;

    const wsUrl = `${WS_BASE_URL}/ws?token=${encodeURIComponent(token)}`;

    try {
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        reconnectAttemptRef.current = 0;
        updateState(ConnectionState.CONNECTED);
        startHeartbeat();
      };

      ws.onmessage = (event: MessageEvent) => {
        // pong mesajlarını ignore et
        if (event.data === "pong") return;

        try {
          const parsed = JSON.parse(event.data) as WebSocketEvent;
          setLastEvent(parsed);
          onEventRef.current?.(parsed);
        } catch {
          // JSON parse edilemeyen mesajlar ignore edilir (stub aşamasında)
        }
      };

      ws.onclose = () => {
        stopHeartbeat();
        wsRef.current = null;

        if (!intentionalCloseRef.current) {
          scheduleReconnect();
        } else {
          updateState(ConnectionState.DISCONNECTED);
        }
      };

      ws.onerror = () => {
        // onerror'dan sonra onclose tetiklenir — burada sadece loglama
        stopHeartbeat();
      };
    } catch {
      updateState(ConnectionState.FAILED);
    }
  }, [updateState, startHeartbeat, stopHeartbeat, scheduleReconnect]);

  // ---------------------------------------------------------------------------
  // Disconnect
  // ---------------------------------------------------------------------------

  const disconnect = useCallback(() => {
    intentionalCloseRef.current = true;

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    stopHeartbeat();

    if (wsRef.current) {
      wsRef.current.close(1000, "Client disconnect");
      wsRef.current = null;
    }

    reconnectAttemptRef.current = 0;
    updateState(ConnectionState.DISCONNECTED);
  }, [stopHeartbeat, updateState]);

  // ---------------------------------------------------------------------------
  // Reconnect (public API)
  // ---------------------------------------------------------------------------

  const reconnect = useCallback(() => {
    disconnect();
    // Kısa gecikme ile yeniden bağlan
    setTimeout(() => {
      intentionalCloseRef.current = false;
      reconnectAttemptRef.current = 0;
      connect();
    }, 100);
  }, [disconnect, connect]);

  // ---------------------------------------------------------------------------
  // Send Message
  // ---------------------------------------------------------------------------

  const sendMessage = useCallback((data: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(data);
    }
  }, []);

  // ---------------------------------------------------------------------------
  // Lifecycle
  // ---------------------------------------------------------------------------

  useEffect(() => {
    // WebSocket devre dışı ise bağlantı kurma
    if (!WS_ENABLED || !enabled) {
      return;
    }

    connect();

    return () => {
      intentionalCloseRef.current = true;
      disconnect();
    };
  }, [enabled]); // eslint-disable-line react-hooks/exhaustive-deps

  // ---------------------------------------------------------------------------
  // Devre dışı durumda sabit değerler dön
  // ---------------------------------------------------------------------------

  if (!WS_ENABLED || !enabled) {
    return {
      connectionState: ConnectionState.DISCONNECTED,
      isConnected: false,
      lastEvent: null,
      sendMessage: () => {},
      disconnect: () => {},
      reconnect: () => {},
    };
  }

  return {
    connectionState,
    isConnected: connectionState === ConnectionState.CONNECTED,
    lastEvent,
    sendMessage,
    disconnect,
    reconnect,
  };
}
