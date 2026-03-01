"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type {
  Property,
  PropertyFilters,
  PaginatedResponse,
} from "@/types/property";

// ─── Backend API Response (search endpoint) ─────────────────────

interface SearchApiResponse {
  items: ApiPropertyItem[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  query: string | null;
}

/** Backend'den gelen property yapısı (frontend Property tipine map edilir) */
interface ApiPropertyItem {
  id: string;
  title: string;
  description?: string | null;
  property_type: string;
  listing_type: string;
  price: number;
  currency: string;
  rooms: string | null;
  gross_area: number | null;
  net_area: number | null;
  floor_number: number | null;
  total_floors: number | null;
  building_age: number | null;
  city: string;
  district: string;
  neighborhood: string | null;
  status: string;
  photos: string[];
  created_at: string;
}

/** Backend property verisini frontend Property tipine dönüştür */
function mapApiToProperty(item: ApiPropertyItem): Property {
  return {
    id: item.id,
    title: item.title,
    property_type: item.property_type as Property["property_type"],
    listing_type: (item.listing_type === "sale" ? "satilik" : "kiralik") as Property["listing_type"],
    price: item.price,
    currency: item.currency,
    area_sqm: item.net_area ?? item.gross_area ?? 0,
    room_count: item.rooms ?? null,
    floor: item.floor_number,
    total_floors: item.total_floors,
    building_age: item.building_age,
    heating_type: null,
    bathroom_count: null,
    furniture_status: null,
    building_type: null,
    facade: null,
    city: item.city,
    district: item.district,
    neighborhood: item.neighborhood,
    address: null,
    status: item.status as Property["status"],
    created_at: item.created_at,
    updated_at: item.created_at, // Backend search'te updated_at yok
  };
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
      if (filters.property_type !== "all") sp.set("property_type", filters.property_type);
      if (filters.status !== "all") sp.set("status", filters.status);

      const res = await api.get<SearchApiResponse>(`/properties/search?${sp.toString()}`);

      return {
        data: res.items.map(mapApiToProperty),
        total: res.total,
        page: res.page,
        per_page: res.per_page,
        total_pages: res.total_pages,
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
    mutationFn: (data: Partial<Property>) => api.post<Property>("/properties", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["properties"] });
    },
  });
}

// ─── useUpdateProperty: İlan güncelleme ─────────────────────────

export function useUpdateProperty() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Property> }) =>
      api.patch<Property>(`/properties/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["properties"] });
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
