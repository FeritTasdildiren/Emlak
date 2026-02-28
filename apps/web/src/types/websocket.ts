/**
 * Emlak Teknoloji Platformu - WebSocket Type Definitions
 *
 * Backend ile senkron tutulan WebSocket event tipleri.
 * Backend karşılığı: apps/api/src/modules/realtime/events.py
 *
 * ÖNEMLİ: EventType enum değerleri değiştirildiğinde
 * backend events.py dosyası da güncellenmelidir.
 */

// ---------------------------------------------------------------------------
// Event Types — Backend EventType enum ile birebir eşleşir
// ---------------------------------------------------------------------------

export enum EventType {
  NOTIFICATION = "notification",
  MATCH_UPDATE = "match_update",
  VALUATION_COMPLETE = "valuation_complete",
  SYSTEM = "system",
}

// ---------------------------------------------------------------------------
// Event Payload Types — Her event tipi için spesifik payload yapısı
// ---------------------------------------------------------------------------

export interface NotificationPayload {
  notification_id: string;
  type: string;
  title: string;
  body?: string | null;
}

export interface MatchUpdatePayload {
  match_id: string;
  customer_id: string;
  property_id: string;
  score: number;
}

export interface ValuationCompletePayload {
  valuation_id: string;
  estimated_price: number;
  confidence?: number;
}

export interface SystemPayload {
  message: string;
  [key: string]: unknown;
}

// ---------------------------------------------------------------------------
// Discriminated Union — Type-safe event handling
// ---------------------------------------------------------------------------

export type WebSocketEventPayload =
  | { type: EventType.NOTIFICATION; payload: NotificationPayload }
  | { type: EventType.MATCH_UPDATE; payload: MatchUpdatePayload }
  | { type: EventType.VALUATION_COMPLETE; payload: ValuationCompletePayload }
  | { type: EventType.SYSTEM; payload: SystemPayload };

// ---------------------------------------------------------------------------
// WebSocket Event — Tüm event'lerin ortak yapısı
// ---------------------------------------------------------------------------

export interface WebSocketEvent {
  type: EventType;
  payload: Record<string, unknown>;
  timestamp: string;
}

// ---------------------------------------------------------------------------
// Connection State — Hook içerisinde bağlantı durumu takibi
// ---------------------------------------------------------------------------

export enum ConnectionState {
  /** Bağlantı henüz kurulmadı veya devre dışı */
  DISCONNECTED = "disconnected",
  /** Bağlantı kuruluyor */
  CONNECTING = "connecting",
  /** Bağlantı aktif, mesaj alışverişine hazırdır */
  CONNECTED = "connected",
  /** Bağlantı koptu, yeniden bağlantı deneniyor */
  RECONNECTING = "reconnecting",
  /** Maksimum yeniden deneme sayısı aşıldı veya kalıcı hata */
  FAILED = "failed",
}

// ---------------------------------------------------------------------------
// Hook Return Type
// ---------------------------------------------------------------------------

export interface UseWebSocketReturn {
  /** Mevcut bağlantı durumu */
  connectionState: ConnectionState;
  /** Bağlantı aktif mi? (connectionState === CONNECTED kısayolu) */
  isConnected: boolean;
  /** Son alınan event */
  lastEvent: WebSocketEvent | null;
  /** Manuel olarak mesaj gönder (stub: echo için) */
  sendMessage: (data: string) => void;
  /** Bağlantıyı kapat ve yeniden denemeyi durdur */
  disconnect: () => void;
  /** Bağlantıyı yeniden başlat */
  reconnect: () => void;
}
