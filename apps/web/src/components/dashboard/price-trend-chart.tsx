"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import type { Payload } from "recharts/types/component/DefaultTooltipContent";
import { cn } from "@/lib/utils";
import { TrendingUp, TrendingDown } from "lucide-react";

interface PriceTrendChartProps {
  trends: Array<{
    month: string;
    avgPriceSqm: number | null;
    sampleCount?: number;
  }>;
  changePct?: number | null;
  type?: "sale" | "rent";
  height?: number;
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: ReadonlyArray<Payload<number, string>>;
  label?: string;
}

function formatPriceSqm(value: number): string {
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}k`;
  }
  return value.toLocaleString("tr-TR");
}

function CustomTooltip({ active, payload, label }: CustomTooltipProps) {
  if (!active || !payload || payload.length === 0) return null;

  const data = payload[0]?.payload as
    | {
        month: string;
        avgPriceSqm: number | null;
        sampleCount?: number;
      }
    | undefined;

  if (!data || data.avgPriceSqm === null) return null;

  return (
    <div className="rounded-lg border bg-white px-3 py-2 shadow-md">
      <p className="text-sm font-semibold text-gray-900">{label}</p>
      <p className="text-sm text-gray-600">
        <span className="font-medium text-primary">
          {data.avgPriceSqm.toLocaleString("tr-TR")} ₺/m²
        </span>
      </p>
      {data.sampleCount !== undefined && (
        <p className="text-xs text-gray-400">{data.sampleCount} ilan</p>
      )}
    </div>
  );
}

export function PriceTrendChart({
  trends,
  changePct,
  type = "sale",
  height = 300,
}: PriceTrendChartProps) {
  const lineColor = type === "sale" ? "#6366f1" : "#10b981";

  const chartData = trends.map((item) => ({
    ...item,
    value: item.avgPriceSqm,
  }));

  const hasData = chartData.some((d) => d.value !== null);

  if (!hasData) {
    return (
      <div
        className="flex items-center justify-center rounded-lg border border-dashed bg-muted/20 text-sm text-muted-foreground"
        style={{ height }}
      >
        Fiyat trendi verisi bulunamadı
      </div>
    );
  }

  return (
    <div className="relative w-full">
      {/* Change percentage badge */}
      {changePct !== undefined && changePct !== null && (
        <div className="absolute right-0 top-0 z-10">
          <div
            className={cn(
              "inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-semibold",
              changePct >= 0
                ? "bg-green-50 text-green-700"
                : "bg-red-50 text-red-700"
            )}
          >
            {changePct >= 0 ? (
              <TrendingUp className="h-3 w-3" />
            ) : (
              <TrendingDown className="h-3 w-3" />
            )}
            {changePct >= 0 ? "+" : ""}
            {changePct.toFixed(1)}%
          </div>
        </div>
      )}

      <ResponsiveContainer width="100%" height={height}>
        <LineChart
          data={chartData}
          margin={{ top: 8, right: 8, left: 0, bottom: 0 }}
        >
          <CartesianGrid
            strokeDasharray="3 3"
            stroke="#f1f5f9"
            vertical={false}
          />
          <XAxis
            dataKey="month"
            tick={{ fontSize: 12, fill: "#94a3b8" }}
            tickLine={false}
            axisLine={{ stroke: "#e2e8f0" }}
          />
          <YAxis
            tickFormatter={formatPriceSqm}
            tick={{ fontSize: 12, fill: "#94a3b8" }}
            tickLine={false}
            axisLine={false}
            width={50}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            type="monotone"
            dataKey="value"
            stroke={lineColor}
            strokeWidth={2.5}
            dot={{ fill: lineColor, r: 3, strokeWidth: 0 }}
            activeDot={{
              fill: lineColor,
              r: 5,
              strokeWidth: 2,
              stroke: "#fff",
            }}
            connectNulls
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
