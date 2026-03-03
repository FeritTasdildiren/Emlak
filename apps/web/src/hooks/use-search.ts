import { useQuery } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import type {
  SearchFilters,
  SearchResponse,
  SuggestionsResponse,
} from "@/types/property";
import { api } from "@/lib/api-client";
import { mapApiToProperty, type ApiProperty } from "@/lib/property-mapper";

// --- API implementations ---

async function fetchSearch(filters: SearchFilters): Promise<SearchResponse> {
  const params = new URLSearchParams();
  if (filters.q) params.set("q", filters.q);
  if (filters.city) params.set("city", filters.city);
  if (filters.district) params.set("district", filters.district);
  if (filters.property_type !== "all")
    params.set("property_type", filters.property_type);
  if (filters.listing_type !== "all") {
    const apiListingType = filters.listing_type === "satilik" ? "sale" : "rent";
    params.set("listing_type", apiListingType);
  }
  if (filters.status !== "all") {
    params.set("status", filters.status);
  } else {
    params.set("status", "all");
  }
  if (filters.min_price !== undefined)
    params.set("min_price", String(filters.min_price));
  if (filters.max_price !== undefined)
    params.set("max_price", String(filters.max_price));
  if (filters.min_area !== undefined)
    params.set("min_area", String(filters.min_area));
  if (filters.max_area !== undefined)
    params.set("max_area", String(filters.max_area));
  if (filters.sort) params.set("sort", filters.sort);
  params.set("page", String(filters.page));
  params.set("per_page", String(filters.per_page));

  const res = await api.get<{
    items: ApiProperty[];
    total: number;
    page: number;
    per_page: number;
    total_pages?: number;
    query: string;
  }>(`/properties/search?${params.toString()}`);

  const total = res.total || 0;
  const per_page = res.per_page || 10;
  const total_pages = res.total_pages || Math.ceil(total / per_page);

  return {
    ...res,
    items: res.items.map(mapApiToProperty),
    total,
    per_page,
    total_pages: total_pages || 1,
    query: res.query || "",
  };
}

async function fetchSuggestions(query: string): Promise<string[]> {
  const params = new URLSearchParams({ q: query, limit: "5" });
  const data = await api.get<SuggestionsResponse>(
    `/properties/search/suggestions?${params.toString()}`
  );
  return data.suggestions;
}

// --- Hooks ---

export const searchKeys = {
  all: ["property-search"] as const,
  search: (filters: SearchFilters) =>
    [...searchKeys.all, "list", filters] as const,
  suggestions: (query: string) =>
    [...searchKeys.all, "suggestions", query] as const,
};

export function usePropertySearch(filters: SearchFilters) {
  return useQuery({
    queryKey: searchKeys.search(filters),
    queryFn: () => fetchSearch(filters),
    staleTime: 2 * 60 * 1000,     // 2 dakika
    gcTime: 5 * 60 * 1000,         // 5 dakika (gcTime >= staleTime)
  });
}

export function useSearchSuggestions(query: string) {
  const [debouncedQuery, setDebouncedQuery] = useState(query);

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedQuery(query), 300);
    return () => clearTimeout(timer);
  }, [query]);

  return useQuery({
    queryKey: searchKeys.suggestions(debouncedQuery),
    queryFn: () => fetchSuggestions(debouncedQuery),
    enabled: debouncedQuery.length >= 2,
    staleTime: 5 * 60 * 1000,     // 5 dakika
    gcTime: 10 * 60 * 1000,       // 10 dakika (gcTime >= staleTime)
  });
}

export function getDefaultSearchFilters(): SearchFilters {
  return {
    q: "",
    city: "",
    district: "",
    property_type: "all",
    listing_type: "all",
    status: "all",
    min_price: undefined,
    max_price: undefined,
    min_area: undefined,
    max_area: undefined,
    sort: "newest",
    page: 1,
    per_page: 10,
  };
}
