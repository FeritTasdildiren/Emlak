"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  Property,
  PropertyFilters,
  PaginatedResponse,
} from "@/types/property";
import { PropertyFormValues } from "@/components/properties/property-form-schema";
import {
  mapApiToProperty,
  mapPropertyToApi,
  type ApiProperty,
} from "@/lib/property-mapper";

// ─── Backend API Response (search endpoint) ─────────────────────

interface SearchApiResponse {
  items: ApiProperty[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  query: string | null;
}

// ─── useProperties: Ana portföy listesi ─────────────────────────

export function useProperties(filters: PropertyFilters) {
  return useQuery<PaginatedResponse<Property>>({
    queryKey: ["properties", filters],
    queryFn: async (): Promise<PaginatedResponse<Property>> => {
      const sp = new URLSearchParams();
      sp.set("page", String(filters.page));
      sp.set("per_page", String(filters.per_page));

      if (filters.search) sp.set("q", filters.search);
      if (filters.property_type !== "all")
        sp.set("property_type", filters.property_type);
      if (filters.status !== "all") sp.set("status", filters.status);

      const res = await api.get<SearchApiResponse>(
        `/properties/search?${sp.toString()}`
      );

      const total = res.total || 0;
      const per_page = res.per_page || 20;
      const total_pages = res.total_pages || Math.ceil(total / per_page);

      return {
        data: res.items.map(mapApiToProperty),
        total,
        page: res.page || 1,
        per_page,
        total_pages: total_pages || 1,
      };
    },
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });
}

// ─── useCreateProperty: Yeni ilan oluşturma ─────────────────────

export function useCreateProperty() {
  const queryClient = useQueryClient();

  return useMutation({
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    mutationFn: (data: any) =>
      api.post<ApiProperty>("/properties", mapPropertyToApi(data)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["properties"] });
    },
  });
}

// ─── useUpdateProperty: İlan güncelleme ─────────────────────────

export function useUpdateProperty() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      data,
    }: {
      id: string;
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      data: any;
    }) => api.patch<ApiProperty>(`/properties/${id}`, mapPropertyToApi(data)),
    onSuccess: (updatedApiProperty) => {
      queryClient.invalidateQueries({ queryKey: ["properties"] });
      queryClient.setQueryData(
        ["properties", updatedApiProperty.id],
        mapApiToProperty(updatedApiProperty)
      );
    },
  });
}

// ─── useDeleteProperty: Ilan silme ──────────────────────────────

export function useDeleteProperty() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/properties/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["properties"] });
    },
  });
}
