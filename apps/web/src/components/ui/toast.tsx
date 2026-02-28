"use client";

import * as React from "react";
import { create } from "zustand";
import { cn } from "@/lib/utils";
import { CheckCircle2, XCircle, Info, X } from "lucide-react";

// ---------------------------------------------------------------------------
// Toast Store (Zustand)
// ---------------------------------------------------------------------------

type ToastVariant = "success" | "error" | "info";

interface ToastItem {
  id: string;
  message: string;
  variant: ToastVariant;
}

interface ToastState {
  toasts: ToastItem[];
  add: (message: string, variant?: ToastVariant) => void;
  remove: (id: string) => void;
}

export const useToastStore = create<ToastState>((set) => ({
  toasts: [],
  add: (message, variant = "success") => {
    const id = crypto.randomUUID();
    set((s) => ({ toasts: [...s.toasts, { id, message, variant }] }));
    // Auto-dismiss after 3 seconds
    setTimeout(() => {
      set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) }));
    }, 3000);
  },
  remove: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}));

// Convenience helper so callers don't need the store directly
export function toast(message: string, variant?: ToastVariant) {
  useToastStore.getState().add(message, variant);
}

// ---------------------------------------------------------------------------
// Icons per variant
// ---------------------------------------------------------------------------

const variantIcon: Record<ToastVariant, typeof CheckCircle2> = {
  success: CheckCircle2,
  error: XCircle,
  info: Info,
};

const variantStyles: Record<ToastVariant, string> = {
  success: "border-emerald-200 bg-emerald-50 text-emerald-800",
  error: "border-red-200 bg-red-50 text-red-800",
  info: "border-blue-200 bg-blue-50 text-blue-800",
};

const iconStyles: Record<ToastVariant, string> = {
  success: "text-emerald-500",
  error: "text-red-500",
  info: "text-blue-500",
};

// ---------------------------------------------------------------------------
// Toast Container — place once in root layout
// ---------------------------------------------------------------------------

export function ToastContainer() {
  const toasts = useToastStore((s) => s.toasts);
  const remove = useToastStore((s) => s.remove);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 max-w-sm">
      {toasts.map((t) => {
        const Icon = variantIcon[t.variant];
        return (
          <div
            key={t.id}
            className={cn(
              "flex items-center gap-3 rounded-lg border px-4 py-3 shadow-lg animate-in slide-in-from-right-5 fade-in duration-300",
              variantStyles[t.variant],
            )}
          >
            <Icon className={cn("h-5 w-5 shrink-0", iconStyles[t.variant])} />
            <p className="flex-1 text-sm font-medium">{t.message}</p>
            <button
              onClick={() => remove(t.id)}
              className="shrink-0 rounded p-0.5 hover:bg-black/5 transition-colors"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        );
      })}
    </div>
  );
}
