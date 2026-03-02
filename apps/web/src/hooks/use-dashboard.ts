"use client";

import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api-client";

export interface DashboardStats {
  portfolio_count: number;
  active_portfolio_count: number;
  customer_count: number;
  customers_by_status: Record<string, number>;
  valuation_count_this_month: number;
  unread_notification_count: number;
  recent_activities: Array<{
    id: string;
    type: string;
    title: string;
    description: string;
    created_at: string;
  }>;
  upcoming_appointments: Array<{
    id: string;
    title: string;
    appointment_date: string;
    customer_name: string | null;
    status: string;
  }>;
}

/**
 * Dashboard istatistiklerini getiren hook.
 * GET /dashboard/stats endpoint'ini kullanır.
 */
export function useDashboard() {
  const query = useQuery<DashboardStats, ApiError>({
    queryKey: ["dashboard", "stats"],
    queryFn: () => api.get<DashboardStats>("/dashboard/stats"),
    staleTime: 5 * 60 * 1000, // 5 dakika
  });

  return {
    stats: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
