"use client";

import { useState } from "react";
import {
  Bell,
  Users,
  Home,
  AlertTriangle,
  BarChart,
  Trash2,
  CheckCheck,
  Loader2,
  MessageSquare,
} from "lucide-react";
import {
  useNotifications,
  useUnreadCount,
  useMarkAsRead,
  useMarkAllAsRead,
  useDeleteNotification,
} from "@/hooks/use-notifications";
import type { NotificationType } from "@/types/notification";

// ─── Relative Time (date-fns kullanmadan) ───────────────────────

function relativeTime(dateStr: string): string {
  const now = Date.now();
  const date = new Date(dateStr).getTime();
  const diffMs = now - date;

  if (diffMs < 0) return "az önce";

  const seconds = Math.floor(diffMs / 1000);
  if (seconds < 60) return "az önce";

  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} dk önce`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} saat önce`;

  const days = Math.floor(hours / 24);
  if (days < 7) return `${days} gün önce`;

  const weeks = Math.floor(days / 7);
  if (weeks < 4) return `${weeks} hafta önce`;

  const months = Math.floor(days / 30);
  if (months < 12) return `${months} ay önce`;

  const years = Math.floor(days / 365);
  return `${years} yıl önce`;
}

// ─── Tip'e göre ikon seçimi ─────────────────────────────────────

function getNotificationIcon(type: NotificationType) {
  switch (type) {
    case "new_match":
      return Users;
    case "new_message":
      return MessageSquare;
    case "valuation":
      return Home;
    case "listing":
      return BarChart;
    case "quota":
      return AlertTriangle;
    case "system":
    default:
      return Bell;
  }
}

function getNotificationIconColor(type: NotificationType): string {
  switch (type) {
    case "new_match":
      return "bg-purple-100 text-purple-600";
    case "new_message":
      return "bg-blue-100 text-blue-600";
    case "valuation":
      return "bg-green-100 text-green-600";
    case "listing":
      return "bg-orange-100 text-orange-600";
    case "quota":
      return "bg-amber-100 text-amber-600";
    case "system":
    default:
      return "bg-gray-100 text-gray-600";
  }
}

// ─── Skeleton Kart ──────────────────────────────────────────────

function SkeletonCard() {
  return (
    <div className="flex items-start gap-4 p-4 border border-gray-200 rounded-lg animate-pulse">
      <div className="w-10 h-10 rounded-full bg-gray-200 shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-gray-200 rounded w-1/3" />
        <div className="h-3 bg-gray-200 rounded w-2/3" />
      </div>
      <div className="h-3 bg-gray-200 rounded w-16 shrink-0" />
    </div>
  );
}

// ─── Page Constants ─────────────────────────────────────────────

const PER_PAGE = 20;

// ─── Mesajlar (Bildirim Merkezi) Sayfası ────────────────────────

export default function MessagesPage() {
  const [activeTab, setActiveTab] = useState<"all" | "unread">("all");
  const [offset, setOffset] = useState(0);

  // Queries
  const {
    data: notificationsData,
    isLoading,
    isError,
  } = useNotifications({
    unreadOnly: activeTab === "unread",
    limit: PER_PAGE,
    offset,
  });

  const { data: unreadData } = useUnreadCount();

  // Mutations
  const markAsRead = useMarkAsRead();
  const markAllAsRead = useMarkAllAsRead();
  const deleteNotification = useDeleteNotification();

  const notifications = notificationsData?.items ?? [];
  const total = notificationsData?.total ?? 0;
  const unreadCount = unreadData?.count ?? 0;
  const hasMore = offset + PER_PAGE < total;

  const handleTabChange = (tab: "all" | "unread") => {
    setActiveTab(tab);
    setOffset(0);
  };

  const handleLoadMore = () => {
    setOffset((prev) => prev + PER_PAGE);
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 w-full max-w-3xl mx-auto space-y-6">
      {/* ── Üst Bar ──────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">Mesajlar</h1>
          {unreadCount > 0 && (
            <span className="inline-flex items-center justify-center min-w-[22px] h-[22px] px-1.5 rounded-full text-xs font-semibold bg-red-500 text-white">
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
        </div>

        {unreadCount > 0 && (
          <button
            onClick={() => markAllAsRead.mutate()}
            disabled={markAllAsRead.isPending}
            className="inline-flex items-center gap-2 px-3 py-2 text-sm font-medium text-blue-700 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {markAllAsRead.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <CheckCheck className="w-4 h-4" />
            )}
            Tümünü Okundu İşaretle
          </button>
        )}
      </div>

      {/* ── Tab Filtreleri ────────────────────────────────────── */}
      <div className="flex gap-1 p-1 bg-gray-100 rounded-lg w-fit">
        <button
          onClick={() => handleTabChange("all")}
          className={
            activeTab === "all"
              ? "px-4 py-1.5 text-sm font-medium rounded-md bg-white text-gray-900 shadow-sm"
              : "px-4 py-1.5 text-sm font-medium rounded-md text-gray-600 hover:text-gray-900 transition-colors"
          }
        >
          Tümü
        </button>
        <button
          onClick={() => handleTabChange("unread")}
          className={
            activeTab === "unread"
              ? "px-4 py-1.5 text-sm font-medium rounded-md bg-white text-gray-900 shadow-sm"
              : "px-4 py-1.5 text-sm font-medium rounded-md text-gray-600 hover:text-gray-900 transition-colors"
          }
        >
          Okunmamış
          {unreadCount > 0 && (
            <span className="ml-1.5 inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-semibold bg-red-500 text-white">
              {unreadCount > 99 ? "99+" : unreadCount}
            </span>
          )}
        </button>
      </div>

      {/* ── Loading State ────────────────────────────────────── */}
      {isLoading && (
        <div className="space-y-3">
          <SkeletonCard />
          <SkeletonCard />
          <SkeletonCard />
        </div>
      )}

      {/* ── Error State ──────────────────────────────────────── */}
      {isError && (
        <div className="border border-red-200 bg-red-50 rounded-lg p-6 text-center">
          <AlertTriangle className="w-8 h-8 text-red-400 mx-auto mb-2" />
          <p className="text-sm text-red-700">
            Bildirimler yüklenirken bir hata oluştu. Lütfen tekrar deneyin.
          </p>
        </div>
      )}

      {/* ── Boş Durum ────────────────────────────────────────── */}
      {!isLoading && !isError && notifications.length === 0 && (
        <div className="border border-gray-200 bg-white rounded-lg p-12 flex flex-col items-center justify-center text-center">
          <div className="w-16 h-16 bg-gray-100 flex items-center justify-center rounded-full mb-4">
            <Bell className="w-7 h-7 text-gray-400" />
          </div>
          <h2 className="text-lg font-semibold text-gray-900 mb-1">
            {activeTab === "unread"
              ? "Tüm bildirimler okunmuş"
              : "Henüz bildiriminiz yok"}
          </h2>
          <p className="text-sm text-gray-500 max-w-sm">
            {activeTab === "unread"
              ? "Okunmamış bildiriminiz bulunmuyor. Tüm bildirimleri görmek için 'Tümü' sekmesine geçin."
              : "Yeni bildirimler geldiğinde burada görünecektir."}
          </p>
        </div>
      )}

      {/* ── Bildirim Kartları ────────────────────────────────── */}
      {!isLoading && !isError && notifications.length > 0 && (
        <div className="space-y-2">
          {notifications.map((notification) => {
            const Icon = getNotificationIcon(notification.type);
            const iconColor = getNotificationIconColor(notification.type);

            return (
              <div
                key={notification.id}
                className={
                  notification.is_read
                    ? "group flex items-start gap-4 p-4 border border-gray-200 rounded-lg bg-white hover:bg-gray-50 transition-colors cursor-pointer"
                    : "group flex items-start gap-4 p-4 border border-blue-200 rounded-lg bg-blue-50/40 hover:bg-blue-50 transition-colors cursor-pointer"
                }
                onClick={() => {
                  if (!notification.is_read) {
                    markAsRead.mutate(notification.id);
                  }
                }}
              >
                {/* Okunmamış Göstergesi + İkon */}
                <div className="relative shrink-0">
                  {!notification.is_read && (
                    <div className="absolute -left-2 top-1/2 -translate-y-1/2 w-2.5 h-2.5 bg-blue-500 rounded-full" />
                  )}
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center ${iconColor}`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                </div>

                {/* İçerik */}
                <div className="flex-1 min-w-0">
                  <p
                    className={
                      notification.is_read
                        ? "text-sm text-gray-700"
                        : "text-sm font-semibold text-gray-900"
                    }
                  >
                    {notification.title}
                  </p>
                  {notification.body && (
                    <p className="text-sm text-gray-500 mt-0.5 line-clamp-2">
                      {notification.body}
                    </p>
                  )}
                  <p className="text-xs text-gray-400 mt-1">
                    {relativeTime(notification.created_at)}
                  </p>
                </div>

                {/* Silme Butonu */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteNotification.mutate(notification.id);
                  }}
                  disabled={deleteNotification.isPending}
                  className="shrink-0 p-1.5 rounded-md text-gray-400 opacity-0 group-hover:opacity-100 hover:bg-red-50 hover:text-red-500 transition-all"
                  title="Bildirimi sil"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Daha Fazla Yükle ─────────────────────────────────── */}
      {!isLoading && hasMore && (
        <div className="flex justify-center pt-2">
          <button
            onClick={handleLoadMore}
            className="px-6 py-2.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
          >
            Daha fazla yükle
          </button>
        </div>
      )}
    </div>
  );
}
