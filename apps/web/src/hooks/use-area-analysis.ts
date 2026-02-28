import { useQuery } from "@tanstack/react-query";
import { fetchAreaAnalysis, type AreaAnalysisResponse } from "@/lib/api/area";

export function useAreaAnalysis(city: string, district: string) {
  return useQuery<AreaAnalysisResponse>({
    queryKey: ["area-analysis", city, district],
    queryFn: () => fetchAreaAnalysis(city, district),
    // staleTime ve refetchOnWindowFocus kaldırıldı — global default yeterli
  });
}
