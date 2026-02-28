"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DataFreshnessBadge } from "@/components/ui/data-freshness-badge";
import { DataFreshnessTooltip } from "@/components/ui/data-freshness-tooltip";
import { useAreaAnalysis } from "@/hooks/use-area-analysis";
import { TrendingUp, TrendingDown, Users, Car, Coffee, Briefcase, LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface AreaInfoCardProps {
  city: string;
  district: string;
  showDepremRisk?: boolean;
  className?: string;
}

export function AreaInfoCard({ city, district, className }: AreaInfoCardProps) {
  const { data, isLoading, isError, error } = useAreaAnalysis(city, district);

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
          <p>Veri yüklenirken hata oluştu: {(error as Error).message}</p>
        </CardContent>
      </Card>
    );
  }

  if (!data) return null;

  return (
    <Card className={cn("h-full", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-lg font-bold">
          {data.district} / {data.city} Analizi
        </CardTitle>
        <DataFreshnessTooltip
          refreshStatus={data.refresh_status}
          lastRefreshedAt={data.last_refreshed_at}
          refreshError={data.refresh_error}
          dataSources={data.data_sources}
        >
          <DataFreshnessBadge 
            status={data.refresh_status} 
            lastRefreshedAt={data.last_refreshed_at}
          />
        </DataFreshnessTooltip>
      </CardHeader>
      <CardContent className="space-y-4 pt-4">
        {/* Fiyatlar */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">Satılık (m²)</p>
            <p className="text-2xl font-bold">
              {data.avg_price_sqm_sale 
                ? new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(data.avg_price_sqm_sale)
                : "-"}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">Kiralık (m²)</p>
            <p className="text-2xl font-bold">
              {data.avg_price_sqm_rent 
                ? new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(data.avg_price_sqm_rent)
                : "-"}
            </p>
          </div>
        </div>

        {/* Trend */}
        <div className="flex items-center space-x-2 text-sm">
           <span className="text-muted-foreground">6 Aylık Trend:</span>
           {data.price_trend_6m !== undefined && (
             <span className={cn(
               "flex items-center font-medium",
               data.price_trend_6m > 0 ? "text-green-600" : "text-red-600"
             )}>
               {data.price_trend_6m > 0 ? <TrendingUp className="w-4 h-4 mr-1" /> : <TrendingDown className="w-4 h-4 mr-1" />}
               %{Math.abs(data.price_trend_6m)}
             </span>
           )}
        </div>

        {/* Skorlar */}
        <div className="grid grid-cols-2 gap-2 pt-2">
           <ScoreItem icon={Car} label="Ulaşım" score={data.transport_score} />
           <ScoreItem icon={Coffee} label="Sosyal" score={data.amenity_score} />
           <ScoreItem icon={Briefcase} label="Yatırım" score={data.investment_score} />
           <ScoreItem icon={Users} label="Nüfus" value={data.population ? `${(data.population / 1000).toFixed(1)}k` : "-"} />
        </div>
      </CardContent>
    </Card>
  );
}

function ScoreItem({ icon: Icon, label, score, value }: { icon: LucideIcon, label: string, score?: number, value?: string }) {
  return (
    <div className="flex items-center space-x-2 bg-muted/40 p-2 rounded-lg">
      <div className="p-1.5 bg-background rounded-md shadow-sm">
        <Icon className="w-4 h-4 text-primary" />
      </div>
      <div>
        <p className="text-[10px] text-muted-foreground uppercase font-semibold">{label}</p>
        <p className="text-sm font-bold">{value || (score !== undefined ? `${score}/100` : "-")}</p>
      </div>
    </div>
  )
}
