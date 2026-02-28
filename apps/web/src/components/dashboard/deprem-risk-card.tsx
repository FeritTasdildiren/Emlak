"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DataFreshnessBadge } from "@/components/ui/data-freshness-badge";
import { DataFreshnessTooltip } from "@/components/ui/data-freshness-tooltip";
import { useDepremRisk } from "@/hooks/use-deprem-risk";
import { cn } from "@/lib/utils";
import { AlertTriangle, Activity, Waves, MapPin } from "lucide-react";

interface DepremRiskCardProps {
  city: string;
  district: string;
  className?: string;
}

export function DepremRiskCard({ city, district, className }: DepremRiskCardProps) {
  const { data, isLoading, isError, error } = useDepremRisk(city, district);

  if (isLoading) {
    return (
      <Card className={cn("h-full animate-pulse", className)}>
        <CardHeader className="h-20 bg-muted/50" />
        <CardContent className="h-40" />
      </Card>
    );
  }

  if (isError) {
    return (
      <Card className={cn("h-full border-red-200 bg-red-50 dark:bg-red-900/10", className)}>
        <CardContent className="flex items-center justify-center h-full p-6 text-red-600 dark:text-red-400">
          <p>Risk verisi alınamadı: {(error as Error).message}</p>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  // Risk rengi belirleme
  const getRiskColor = (score: number) => {
    if (score < 20) return "bg-green-500 text-white";
    if (score < 40) return "bg-yellow-500 text-white";
    if (score < 60) return "bg-orange-500 text-white";
    if (score < 80) return "bg-red-500 text-white";
    return "bg-red-900 text-white";
  };
  
  const riskColorClass = getRiskColor(data.risk_score);

  return (
    <Card className={cn("h-full", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          <CardTitle className="text-lg font-bold">Deprem Riski</CardTitle>
        </div>
        <DataFreshnessTooltip
          refreshStatus={data.refresh_status}
          lastRefreshedAt={data.last_refreshed_at}
          dataSources={data.data_sources}
        >
          <DataFreshnessBadge status={data.refresh_status} />
        </DataFreshnessTooltip>
      </CardHeader>
      <CardContent className="space-y-6 pt-4">
        {/* Ana Skor */}
        <div className="space-y-2">
          <div className="flex justify-between items-end">
             <span className="text-sm font-medium text-muted-foreground">Genel Risk Skoru</span>
             <span className="text-2xl font-bold">{data.risk_score}/100</span>
          </div>
          <div className="h-3 w-full bg-muted rounded-full overflow-hidden">
            <div 
              className={cn("h-full transition-all duration-1000 ease-out", riskColorClass)} 
              style={{ width: `${data.risk_score}%` }}
            />
          </div>
          <div className="flex justify-between text-[10px] text-muted-foreground uppercase">
             <span>Düşük</span>
             <span>Orta</span>
             <span>Yüksek</span>
             <span>Çok Yüksek</span>
          </div>
        </div>

        {/* Detaylar */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-muted/30 p-3 rounded-lg flex flex-col gap-1">
             <div className="flex items-center gap-2 text-xs text-muted-foreground">
               <Activity className="w-3 h-3" />
               <span>PGA Değeri</span>
             </div>
             <span className="font-semibold text-sm">{data.pga_value ? `${data.pga_value} g` : "-"}</span>
          </div>
          <div className="bg-muted/30 p-3 rounded-lg flex flex-col gap-1">
             <div className="flex items-center gap-2 text-xs text-muted-foreground">
               <Waves className="w-3 h-3" />
               <span>Zemin Sınıfı</span>
             </div>
             <span className="font-semibold text-sm">{data.soil_class || "-"}</span>
          </div>
          <div className="bg-muted/30 p-3 rounded-lg flex flex-col gap-1">
             <div className="flex items-center gap-2 text-xs text-muted-foreground">
               <MapPin className="w-3 h-3" />
               <span>Fay Mesafesi</span>
             </div>
             <span className="font-semibold text-sm">{data.fault_distance_km ? `${data.fault_distance_km} km` : "-"}</span>
          </div>
          <div className="bg-muted/30 p-3 rounded-lg flex flex-col gap-1">
             <div className="flex items-center gap-2 text-xs text-muted-foreground">
               <span className="w-3 h-3 block border rounded-sm" />
               <span>Yapı Kodu</span>
             </div>
             <span className="font-semibold text-sm">{data.building_code_era || "-"}</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
