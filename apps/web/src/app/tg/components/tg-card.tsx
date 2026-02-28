"use client";

import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

// ================================================================
// TgCard — Mobil kart bileşeni
// ================================================================

interface TgCardProps {
  children: ReactNode;
  className?: string;
}

export function TgCard({ children, className }: TgCardProps) {
  return (
    <div
      className={cn("rounded-2xl bg-white p-4 shadow-sm", className)}
      style={{
        backgroundColor: "var(--tg-theme-secondary-bg-color, #ffffff)",
      }}
    >
      {children}
    </div>
  );
}
