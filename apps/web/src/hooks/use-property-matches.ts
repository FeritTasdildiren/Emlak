import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import { Match } from "@/types/match";

interface MatchesResponse {
  items: Match[];
  total: number;
  page: number;
  per_page: number;
}

interface CustomerResponse {
  id: string;
  full_name: string;
}

export interface EnrichedMatch extends Match {
  customer_name?: string;
}

export function usePropertyMatches(propertyId: string) {
  const { data, isLoading, isError, refetch } = useQuery<{
    items: EnrichedMatch[];
    total: number;
  }>({
    queryKey: ["matches", "property", propertyId],
    queryFn: async () => {
      const response = await api.get<MatchesResponse>(
        `/matches?property_id=${propertyId}&per_page=50`
      );

      const matches: EnrichedMatch[] = response.items || [];
      if (matches.length === 0) {
        return { items: matches, total: response.total };
      }

      // Unique customer ID'leri topla
      const customerIds = Array.from(
        new Set(matches.map((m) => m.customer_id))
      );

      // Her customer icin isim bilgisi cek
      const customerPromises = customerIds.map((cid) =>
        api
          .get<CustomerResponse>(`/customers/${cid}`)
          .catch(() => null)
      );
      const customers = await Promise.all(customerPromises);

      // customer_id -> full_name map olustur
      const nameMap: Record<string, string> = {};
      customers.forEach((c) => {
        if (c && c.id && c.full_name) {
          nameMap[c.id] = c.full_name;
        }
      });

      // Match'leri zenginlestir
      const enriched = matches.map((m) => ({
        ...m,
        customer_name: nameMap[m.customer_id],
      }));

      return { items: enriched, total: response.total };
    },
    staleTime: 30 * 1000,
    gcTime: 5 * 60 * 1000,
    enabled: !!propertyId,
  });

  return {
    matches: data?.items ?? [],
    total: data?.total ?? 0,
    isLoading,
    isError,
    refetch,
  };
}
