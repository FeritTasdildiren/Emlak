"use client";

import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api-client";
import type { Property } from "@/types/property";

/**
 * Mülk detaylarını getiren hook.
 * GET /properties/{id} endpoint'ini kullanır.
 */
export function usePropertyDetail(id: string) {
  const query = useQuery<Property, ApiError>({
    queryKey: ["properties", id],
    queryFn: () => api.get<Property>(`/properties/${id}`),
    enabled: !!id,
    staleTime: 5 * 60 * 1000,
  });

  return {
    property: query.data,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error,
    refetch: query.refetch,
  };
}
