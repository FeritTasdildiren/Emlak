"use client";

import { cn } from "@/lib/utils";

// ================================================================
// TgSkeleton — Loading state skeleton bileşeni
// ================================================================

interface TgSkeletonProps {
  className?: string;
}

export function TgSkeleton({ className }: TgSkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-2xl bg-slate-200",
        className,
      )}
    />
  );
}
