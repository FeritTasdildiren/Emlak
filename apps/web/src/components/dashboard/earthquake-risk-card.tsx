import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EarthquakeRiskBadge } from "@/components/dashboard/earthquake-risk-badge";
import { cn } from "@/lib/utils";
import { AlertTriangle, MapPin, Waves, Activity } from "lucide-react";

interface EarthquakeRiskCardProps {
  score: number;
  riskLevel: "low" | "medium" | "high" | "critical";
  faultDistanceKm?: number;
  soilClass?: string;
  pgaValue?: number;
  showDisclaimer?: boolean;
}

const FAULT_DISTANCE_MAX_KM = 50;

const RISK_LEVEL_LABELS: Record<EarthquakeRiskCardProps["riskLevel"], string> = {
  low: "Düşük Risk",
  medium: "Orta Risk",
  high: "Yüksek Risk",
  critical: "Kritik Risk",
};

function FaultDistanceBar({ distanceKm }: { distanceKm: number }) {
  // Closer = more risky (red). Further = safer (green).
  const clampedKm = Math.max(0, Math.min(distanceKm, FAULT_DISTANCE_MAX_KM));
  const pct = (clampedKm / FAULT_DISTANCE_MAX_KM) * 100;

  // Invert for color: close distance = danger
  const barColor =
    clampedKm < 10
      ? "bg-rose-500"
      : clampedKm < 25
        ? "bg-orange-500"
        : "bg-emerald-500";

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between text-xs">
        <div className="flex items-center gap-1.5 text-muted-foreground">
          <MapPin className="h-3 w-3" />
          <span>Fay Hattı Mesafesi</span>
        </div>
        <span className="font-semibold">{distanceKm} km</span>
      </div>
      <div className="h-2 w-full rounded-full bg-muted overflow-hidden">
        <div
          className={cn("h-full rounded-full transition-all duration-700 ease-out", barColor)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px] text-muted-foreground">
        <span>0 km</span>
        <span>{FAULT_DISTANCE_MAX_KM} km</span>
      </div>
    </div>
  );
}

export function EarthquakeRiskCard({
  score,
  riskLevel,
  faultDistanceKm,
  soilClass,
  pgaValue,
  showDisclaimer = true,
}: EarthquakeRiskCardProps) {
  return (
    <Card className="h-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 text-orange-500" />
          <CardTitle className="text-lg font-bold">Deprem Riski</CardTitle>
        </div>
        <span
          className={cn(
            "rounded-full px-2 py-0.5 text-xs font-semibold",
            riskLevel === "low" && "bg-emerald-50 text-emerald-700",
            riskLevel === "medium" && "bg-yellow-50 text-yellow-700",
            riskLevel === "high" && "bg-orange-50 text-orange-700",
            riskLevel === "critical" && "bg-rose-50 text-rose-700"
          )}
        >
          {RISK_LEVEL_LABELS[riskLevel]}
        </span>
      </CardHeader>

      <CardContent className="space-y-6 pt-4">
        {/* Risk Badge */}
        <div className="flex justify-center">
          <EarthquakeRiskBadge
            score={score}
            riskLevel={riskLevel}
            size="lg"
            showLabel
          />
        </div>

        {/* Fault Distance Bar */}
        {faultDistanceKm !== undefined && (
          <FaultDistanceBar distanceKm={faultDistanceKm} />
        )}

        {/* Detail Grid */}
        <div className="grid grid-cols-2 gap-3">
          {soilClass !== undefined && (
            <div className="flex flex-col gap-1 rounded-lg bg-muted/30 p-3">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Waves className="h-3 w-3" />
                <span>Zemin Sınıfı</span>
              </div>
              <span className="text-sm font-semibold">{soilClass}</span>
            </div>
          )}
          {pgaValue !== undefined && (
            <div className="flex flex-col gap-1 rounded-lg bg-muted/30 p-3">
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                <Activity className="h-3 w-3" />
                <span>PGA Değeri</span>
              </div>
              <span className="text-sm font-semibold">{pgaValue} g</span>
            </div>
          )}
        </div>

        {/* Disclaimer */}
        {showDisclaimer && (
          <div className="flex gap-2 rounded-lg bg-yellow-50 p-3">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-yellow-600" />
            <p className="text-xs leading-relaxed text-yellow-800">
              Bu skor tahmini bir değerdir ve kesin mühendislik değerlendirmesi
              yerine geçmez. Detaylı analiz için uzman görüşü alınız.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
