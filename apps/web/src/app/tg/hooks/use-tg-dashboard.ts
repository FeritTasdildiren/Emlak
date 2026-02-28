"use client";

import { useQuery } from "@tanstack/react-query";
import {
  fetchPropertyCount,
  fetchCustomerCount,
  fetchMatchCount,
  fetchCreditBalance,
  humanizeError,
  type CreditBalance,
} from "@/app/tg/lib/tg-api";

// ================================================================
// Types
// ================================================================

export interface DashboardData {
  propertyCount: number;
  customerCount: number;
  matchCount: number;
  credit: CreditBalance;
}

// ================================================================
// Hook
// ================================================================

/**
 * Dashboard verilerini paralel olarak ceken React Query hook.
 * staleTime 5dk — arka planda yenilenebilir, ama gereksiz refetch yok.
 */
export function useTgDashboard() {
  const query = useQuery<DashboardData, Error>({
    queryKey: ["tg", "dashboard"],
    queryFn: async () => {
      const [propertyCount, customerCount, matchCount, credit] =
        await Promise.all([
          fetchPropertyCount(),
          fetchCustomerCount(),
          fetchMatchCount(),
          fetchCreditBalance(),
        ]);

      return { propertyCount, customerCount, matchCount, credit };
    },
    staleTime: 5 * 60 * 1000, // 5 dakika
    retry: 2,
  });

  return {
    data: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error ? humanizeError(query.error) : null,
    refetch: query.refetch,
  };
}
