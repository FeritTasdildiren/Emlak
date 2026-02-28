import { useQuery } from "@tanstack/react-query";
import { fetchAreaTrends } from "@/lib/api/area";

export function useAreaTrends(city: string, district: string, months?: number) {
  return useQuery({
    queryKey: ["area-trends", city, district, months],
    queryFn: () => fetchAreaTrends(city, district, months),
    enabled: !!city && !!district,
    staleTime: 30 * 60 * 1000,  // 30 dakika — trend verisi seyrek değişir
    gcTime: 60 * 60 * 1000,     // 60 dakika (gcTime >= staleTime ZORUNLU)
  });
}
