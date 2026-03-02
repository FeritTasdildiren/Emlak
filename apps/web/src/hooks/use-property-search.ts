"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { SearchableSelectOption } from "@/components/ui/searchable-select";

interface ApiPropertyItem {
  id: string;
  title: string;
  price: number;
  currency: string;
  rooms: string | null;
  gross_area: number | null;
  net_area: number | null;
  city: string;
  district: string;
}

interface SearchApiResponse {
  items: ApiPropertyItem[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  query: string | null;
}

const formatPrice = new Intl.NumberFormat("tr-TR", {
  style: "currency",
  currency: "TRY",
  maximumFractionDigits: 0,
});

export function usePropertySearch(query: string) {
  return useQuery({
    queryKey: ["properties-search", query],
    queryFn: async (): Promise<SearchableSelectOption[]> => {
      const sp = new URLSearchParams();
      sp.set("per_page", "20");
      sp.set("page", "1");
      if (query.length >= 2) {
        sp.set("q", query);
      }

      const res = await api.get<SearchApiResponse>(`/properties/search?${sp.toString()}`);

      return res.items.map((item) => ({
        value: item.id,
        label: item.title,
        sublabel: `${item.city} ${item.district} — ${formatPrice.format(item.price)} — ${item.rooms || "?"} oda ${item.net_area ?? item.gross_area ?? 0} m²`,
      }));
    },
    staleTime: 30 * 1000,
    gcTime: 2 * 60 * 1000,
  });
}
