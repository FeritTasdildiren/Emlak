"use client";

import { useQuery } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api-client";
import type { Property } from "@/types/property";
import { mapApiToProperty, type ApiProperty } from "@/lib/property-mapper";

/**
 * Mülk detaylarını getiren hook.
 * GET /properties/{id} endpoint'ini kullanır.
 */
export function usePropertyDetail(id: string) {
  const query = useQuery<Property, ApiError>({
    queryKey: ["properties", id],
    queryFn: async () => {
      const res = await api.get<ApiProperty>(`/properties/${id}`);
      return mapApiToProperty(res);
    },
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
