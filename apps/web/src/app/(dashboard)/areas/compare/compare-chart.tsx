"use client";

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";
import type { NameType, ValueType } from "recharts/types/component/DefaultTooltipContent";
import type { CompareAreaItem } from "@/lib/api/area";

interface CompareChartProps {
  areas: CompareAreaItem[];
}

const formatCurrency = (val: number) =>
  new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency: "TRY",
    maximumFractionDigits: 0,
  }).format(val);

export default function CompareChart({ areas }: CompareChartProps) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        data={areas}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
      >
        <CartesianGrid strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="district" />
        <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
        <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
        <Tooltip
          formatter={(
            value: ValueType | undefined,
            name: NameType | undefined
          ) => {
            if (typeof value !== "number") return [value, name];
            return [
              formatCurrency(value),
              name === "avg_price_sqm_sale" ? "Satış m²" : "Kira m²",
            ];
          }}
        />
        <Legend />
        <Bar
          yAxisId="left"
          dataKey="avg_price_sqm_sale"
          name="Satış m²"
          fill="#8884d8"
          radius={[4, 4, 0, 0]}
        />
        <Bar
          yAxisId="right"
          dataKey="avg_price_sqm_rent"
          name="Kira m²"
          fill="#82ca9d"
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
