import { useQuery } from "@tanstack/react-query";
import { fetchAreaCompare } from "@/lib/api/area";

export function useAreaCompare(districts: string[]) {
  return useQuery({
    queryKey: ["area-compare", districts],
    queryFn: () => fetchAreaCompare(districts),
    enabled: districts.length > 0,
    staleTime: 15 * 60 * 1000,  // 15 dakika — karşılaştırma verisi seyrek değişir
    gcTime: 30 * 60 * 1000,     // 30 dakika (gcTime >= staleTime ZORUNLU)
  });
}
