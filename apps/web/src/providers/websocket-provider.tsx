/**
 * Emlak Teknoloji Platformu - WebSocket Provider
 *
 * React Context üzerinden WebSocket bağlantısını tüm uygulamaya sağlar.
 *
 * Kontrol:
 *   - NEXT_PUBLIC_WS_ENABLED=false (varsayılan) → Bağlantı AÇILMAZ, context boş değer döner
 *   - NEXT_PUBLIC_WS_ENABLED=true → WebSocket bağlantısı kurulur
 *
 * Kullanım:
 *   // Layout veya providers.tsx içerisinde:
 *   <WebSocketProvider>
 *     <App />
 *   </WebSocketProvider>
 *
 *   // Herhangi bir component içerisinde:
 *   const { isConnected, lastEvent } = useWebSocketContext();
 *
 * Durum: STUB — temel provider, genişletmeye hazır.
 */

"use client";

import {
  createContext,
  useContext,
  useCallback,
  type ReactNode,
} from "react";
import {
  useWebSocket,
  type UseWebSocketOptions,
} from "@/hooks/use-websocket";
import {
  ConnectionState,
  type UseWebSocketReturn,
  type WebSocketEvent,
} from "@/types/websocket";

// ---------------------------------------------------------------------------
// Context
// ---------------------------------------------------------------------------

const defaultValue: UseWebSocketReturn = {
  connectionState: ConnectionState.DISCONNECTED,
  isConnected: false,
  lastEvent: null,
  sendMessage: () => {},
  disconnect: () => {},
  reconnect: () => {},
};

const WebSocketContext = createContext<UseWebSocketReturn>(defaultValue);

// ---------------------------------------------------------------------------
// Provider
// ---------------------------------------------------------------------------

interface WebSocketProviderProps {
  children: ReactNode;
  /** Global event handler — tüm event'ler için */
  onEvent?: (event: WebSocketEvent) => void;
  /** Provider'ı devre dışı bırak (test vb. için) */
  enabled?: boolean;
}

export function WebSocketProvider({
  children,
  onEvent,
  enabled,
}: WebSocketProviderProps) {
  const handleEvent = useCallback(
    (event: WebSocketEvent) => {
      onEvent?.(event);
    },
    [onEvent]
  );

  const options: UseWebSocketOptions = {
    onEvent: handleEvent,
    enabled,
  };

  const ws = useWebSocket(options);

  return (
    <WebSocketContext.Provider value={ws}>{children}</WebSocketContext.Provider>
  );
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

/**
 * WebSocket context'ine erişim hook'u.
 *
 * WebSocketProvider dışında kullanılırsa varsayılan (disconnected) değer döner.
 * Bu sayede provider olmadan da hata vermez (graceful degradation).
 */
export function useWebSocketContext(): UseWebSocketReturn {
  return useContext(WebSocketContext);
}
