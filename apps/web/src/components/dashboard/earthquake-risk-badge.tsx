import { cn } from "@/lib/utils";

interface EarthquakeRiskBadgeProps {
  score: number; // 0-100
  riskLevel: "low" | "medium" | "high" | "critical";
  size?: "sm" | "md" | "lg"; // 40px, 64px, 96px
  showLabel?: boolean;
}

const RISK_COLORS: Record<EarthquakeRiskBadgeProps["riskLevel"], string> = {
  low: "#10b981", // emerald-500
  medium: "#facc15", // yellow-400
  high: "#f97316", // orange-500
  critical: "#f43f5e", // rose-500
};

const RISK_LABELS: Record<EarthquakeRiskBadgeProps["riskLevel"], string> = {
  low: "Düşük",
  medium: "Orta",
  high: "Yüksek",
  critical: "Kritik",
};

const SIZE_CONFIG = {
  sm: { dimension: 40, strokeWidth: 3, fontSize: 12, labelSize: 7, radius: 16 },
  md: { dimension: 64, strokeWidth: 4, fontSize: 18, labelSize: 9, radius: 26 },
  lg: { dimension: 96, strokeWidth: 5, fontSize: 26, labelSize: 12, radius: 40 },
} as const;

export function EarthquakeRiskBadge({
  score,
  riskLevel,
  size = "md",
  showLabel = true,
}: EarthquakeRiskBadgeProps) {
  const config = SIZE_CONFIG[size];
  const color = RISK_COLORS[riskLevel];
  const label = RISK_LABELS[riskLevel];

  const circumference = 2 * Math.PI * config.radius;
  const clampedScore = Math.max(0, Math.min(100, score));
  const dashOffset = circumference - (clampedScore / 100) * circumference;

  const center = config.dimension / 2;

  return (
    <div
      className="inline-flex flex-col items-center gap-0.5"
      role="img"
      aria-label={`Deprem risk skoru: ${clampedScore}, seviye: ${label}`}
    >
      <svg
        width={config.dimension}
        height={config.dimension}
        viewBox={`0 0 ${config.dimension} ${config.dimension}`}
        className="transform -rotate-90"
      >
        {/* Background circle */}
        <circle
          cx={center}
          cy={center}
          r={config.radius}
          fill="none"
          stroke="#e5e7eb"
          strokeWidth={config.strokeWidth}
        />
        {/* Progress circle */}
        <circle
          cx={center}
          cy={center}
          r={config.radius}
          fill="none"
          stroke={color}
          strokeWidth={config.strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          className="transition-all duration-700 ease-out"
        />
        {/* Score text — rotate back to upright */}
        <text
          x={center}
          y={center}
          textAnchor="middle"
          dominantBaseline="central"
          className="rotate-90 origin-center"
          style={{
            fontSize: config.fontSize,
            fontWeight: 700,
            fill: color,
          }}
        >
          {clampedScore}
        </text>
      </svg>
      {showLabel && (
        <span
          className={cn(
            "font-semibold uppercase tracking-wide text-center leading-none",
          )}
          style={{ fontSize: config.labelSize, color }}
        >
          {label}
        </span>
      )}
    </div>
  );
}
