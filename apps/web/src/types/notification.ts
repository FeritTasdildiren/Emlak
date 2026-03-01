// ─── Notification Types ──────────────────────────────────────────

export type NotificationType =
  | "new_match"
  | "new_message"
  | "valuation"
  | "listing"
  | "system"
  | "quota";

export interface Notification {
  id: string;
  title: string;
  body: string | null;
  type: NotificationType;
  is_read: boolean;
  created_at: string;
  data?: Record<string, unknown>;
}

export interface NotificationListResponse {
  items: Notification[];
  total: number;
}

export interface UnreadCountResponse {
  count: number;
}
