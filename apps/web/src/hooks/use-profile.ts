"use client";

import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api-client";
import type { UserProfile } from "@/types/settings";

/**
 * Kullanıcı profil bilgilerini getiren hook.
 * GET /auth/me endpoint'ini kullanır.
 */
export function useProfile() {
  const query = useQuery<UserProfile, ApiError>({
    queryKey: ["auth", "me"],
    queryFn: () => api.get<UserProfile>("/auth/me"),
    staleTime: 5 * 60 * 1000, // 5 dakika
    gcTime: 10 * 60 * 1000, // 10 dakika (gcTime >= staleTime)
    retry: 2,
  });

  return {
    user: query.data ?? null,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
