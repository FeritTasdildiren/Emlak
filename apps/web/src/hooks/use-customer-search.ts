"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { Customer, CustomerType, LeadStatus } from "@/types/customer";
import { SearchableSelectOption } from "@/components/ui/searchable-select";

interface CustomerListResponse {
  items: Customer[];
  total: number;
  page: number;
  per_page: number;
}

const customerTypeLabel: Record<CustomerType, string> = {
  buyer: "Alıcı",
  seller: "Satıcı",
  renter: "Kiracı",
  landlord: "Ev Sahibi",
};

const leadStatusLabel: Record<LeadStatus, string> = {
  cold: "Soğuk",
  warm: "Ilık",
  hot: "Sıcak",
  converted: "Dönüştü",
  lost: "Kaybedildi",
};

export function useCustomerSearch(query: string) {
  return useQuery({
    queryKey: ["customers-search", query],
    queryFn: async (): Promise<SearchableSelectOption[]> => {
      if (query.length < 2) return [];

      const res = await api.get<CustomerListResponse>(
        `/customers?search=${encodeURIComponent(query)}&per_page=20&page=1`
      );

      return res.items.map((customer) => ({
        value: customer.id,
        label: `${customer.full_name} (${customerTypeLabel[customer.customer_type]})`,
        sublabel: `${customer.phone || "Telefon yok"} — ${leadStatusLabel[customer.lead_status]}`,
      }));
    },
    enabled: query.length >= 2,
    staleTime: 30 * 1000,
    gcTime: 2 * 60 * 1000,
  });
}
