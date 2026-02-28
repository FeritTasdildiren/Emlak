"use client";

import { cn } from "@/lib/utils";
import type { LeadStatus } from "@/types/customer";
import type { PipelineCounts } from "@/hooks/use-customers";

const PIPELINE_ITEMS: {
  status: LeadStatus;
  label: string;
  labelColor: string;
  dotColor: string;
  activeBorder: string;
  activeRing: string;
}[] = [
  {
    status: "cold",
    label: "Soğuk",
    labelColor: "text-gray-500",
    dotColor: "bg-gray-300",
    activeBorder: "border-gray-300",
    activeRing: "ring-1 ring-gray-200",
  },
  {
    status: "warm",
    label: "Ilık",
    labelColor: "text-yellow-700",
    dotColor: "bg-yellow-400",
    activeBorder: "border-yellow-200",
    activeRing: "ring-1 ring-yellow-100",
  },
  {
    status: "hot",
    label: "Sıcak",
    labelColor: "text-red-700",
    dotColor: "bg-red-500",
    activeBorder: "border-red-200",
    activeRing: "ring-1 ring-red-100",
  },
  {
    status: "converted",
    label: "Dönüşüm",
    labelColor: "text-emerald-700",
    dotColor: "bg-emerald-500",
    activeBorder: "border-emerald-200",
    activeRing: "ring-1 ring-emerald-100",
  },
  {
    status: "lost",
    label: "Kayıp",
    labelColor: "text-slate-500",
    dotColor: "bg-slate-400",
    activeBorder: "border-slate-300",
    activeRing: "ring-1 ring-slate-200",
  },
];

interface CustomerPipelineProps {
  counts: PipelineCounts;
  activeStatus: LeadStatus | null;
  onStatusClick: (status: LeadStatus | null) => void;
}

export function CustomerPipeline({
  counts,
  activeStatus,
  onStatusClick,
}: CustomerPipelineProps) {
  return (
    <div className="overflow-x-auto -mx-4 sm:mx-0 pb-2 sm:pb-0">
      <div className="flex gap-4 px-4 sm:px-0 min-w-max">
        {PIPELINE_ITEMS.map((item) => {
          const isActive = activeStatus === item.status;
          return (
            <button
              key={item.status}
              onClick={() =>
                onStatusClick(isActive ? null : item.status)
              }
              className={cn(
                "group flex items-center justify-between w-40 p-3 bg-white border rounded-lg hover:shadow-sm transition-all text-left",
                isActive
                  ? `${item.activeBorder} ${item.activeRing}`
                  : "border-gray-200 hover:border-gray-300"
              )}
            >
              <div>
                <p
                  className={cn(
                    "text-xs font-medium uppercase tracking-wide mb-1",
                    isActive ? item.labelColor : "text-gray-500"
                  )}
                >
                  {item.label}
                </p>
                <span className="text-2xl font-bold text-gray-900">
                  {counts[item.status]}
                </span>
              </div>
              <div
                className={cn(
                  "w-2 h-2 rounded-full",
                  item.dotColor,
                  item.status === "hot" && "animate-pulse"
                )}
              />
            </button>
          );
        })}
      </div>
    </div>
  );
}
