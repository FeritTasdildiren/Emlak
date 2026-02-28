"use client";

import { cn } from "@/lib/utils";

// ================================================================
// SegmentedControl — Yatay scroll, aktif renk orange-600
// ================================================================

interface SegmentedControlProps {
  options: string[];
  value: string;
  onChange: (value: string) => void;
}

export function SegmentedControl({
  options,
  value,
  onChange,
}: SegmentedControlProps) {
  return (
    <div className="flex gap-1.5 overflow-x-auto scrollbar-hide [-ms-overflow-style:none] [scrollbar-width:none] [-webkit-overflow-scrolling:touch] [&::-webkit-scrollbar]:hidden">
      {options.map((option) => {
        const isActive = option === value;
        return (
          <button
            key={option}
            type="button"
            onClick={() => onChange(option)}
            className={cn(
              "flex shrink-0 items-center justify-center rounded-xl px-3.5 py-2.5 text-[13px] font-medium transition-all min-h-[44px]",
              "border-[1.5px]",
              isActive
                ? "border-orange-600 bg-orange-50 text-orange-600"
                : "border-transparent bg-slate-100 text-slate-500",
            )}
            style={
              !isActive
                ? {
                    backgroundColor:
                      "var(--tg-theme-secondary-bg-color, #f1f5f9)",
                    color: "var(--tg-theme-hint-color, #64748b)",
                  }
                : undefined
            }
          >
            {option}
          </button>
        );
      })}
    </div>
  );
}
