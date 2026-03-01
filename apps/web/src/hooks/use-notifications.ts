"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  Notification,
  NotificationListResponse,
  UnreadCountResponse,
} from "@/types/notification";

// ─── Query Keys ──────────────────────────────────────────────────

const NOTIFICATIONS_KEY = "notifications";
const UNREAD_COUNT_KEY = "notifications-unread-count";

// ─── useNotifications: Bildirim listesi ─────────────────────────

export function useNotifications(params: {
  unreadOnly?: boolean;
  limit?: number;
  offset?: number;
}) {
  const { unreadOnly = false, limit = 20, offset = 0 } = params;

  return useQuery({
    queryKey: [NOTIFICATIONS_KEY, { unreadOnly, limit, offset }],
    queryFn: async (): Promise<NotificationListResponse> => {
      const searchParams = new URLSearchParams();
      searchParams.set("limit", String(limit));
      searchParams.set("offset", String(offset));
      if (unreadOnly) searchParams.set("unread_only", "true");

      return api.get<NotificationListResponse>(
        `/notifications?${searchParams.toString()}`
      );
    },
    staleTime: 30 * 1000, // 30sn
    gcTime: 5 * 60 * 1000, // 5dk
  });
}

// ─── useUnreadCount: Okunmamış bildirim sayısı ──────────────────

export function useUnreadCount() {
  return useQuery({
    queryKey: [UNREAD_COUNT_KEY],
    queryFn: () => api.get<UnreadCountResponse>("/notifications/unread-count"),
    staleTime: 10 * 1000, // 10sn
    gcTime: 5 * 60 * 1000, // 5dk
    refetchInterval: 30 * 1000, // 30sn polling
  });
}

// ─── useMarkAsRead: Tekli okundu işaretleme ─────────────────────

export function useMarkAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.patch<Notification>(`/notifications/${id}/read`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [NOTIFICATIONS_KEY] });
      queryClient.invalidateQueries({ queryKey: [UNREAD_COUNT_KEY] });
    },
  });
}

// ─── useMarkAllAsRead: Tümünü okundu işaretleme ────────────────

export function useMarkAllAsRead() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      api.patch<{ updated_count: number }>("/notifications/read-all", {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [NOTIFICATIONS_KEY] });
      queryClient.invalidateQueries({ queryKey: [UNREAD_COUNT_KEY] });
    },
  });
}

// ─── useDeleteNotification: Bildirim silme ──────────────────────

export function useDeleteNotification() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete<void>(`/notifications/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [NOTIFICATIONS_KEY] });
      queryClient.invalidateQueries({ queryKey: [UNREAD_COUNT_KEY] });
    },
  });
}
