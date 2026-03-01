import { useQuery } from "@tanstack/react-query";
import { fetchDepremRisk, type DepremRiskResponse } from "@/lib/api/area";

export function useDepremRisk(city: string, district: string) {
  return useQuery<DepremRiskResponse>({
    queryKey: ["deprem-risk", city, district],
    queryFn: () => fetchDepremRisk(district),
    enabled: !!district,
    staleTime: 30 * 60 * 1000,  // 30 dakika — deprem verisi seyrek değişir
    gcTime: 60 * 60 * 1000,     // 60 dakika (gcTime >= staleTime ZORUNLU)
  });
}
