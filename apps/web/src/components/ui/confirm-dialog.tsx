"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { AlertTriangle } from "lucide-react";

// ---------------------------------------------------------------------------
// ConfirmDialog — modal replacement for window.confirm()
// ---------------------------------------------------------------------------

export interface ConfirmDialogProps {
  open: boolean;
  title?: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: "danger" | "default";
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title = "Emin misiniz?",
  description,
  confirmLabel = "Evet",
  cancelLabel = "Vazgeç",
  variant = "default",
  loading = false,
  onConfirm,
  onCancel,
}: ConfirmDialogProps) {
  // Close on Escape key
  React.useEffect(() => {
    if (!open) return;
    function handleKey(e: KeyboardEvent) {
      if (e.key === "Escape") onCancel();
    }
    document.addEventListener("keydown", handleKey);
    return () => document.removeEventListener("keydown", handleKey);
  }, [open, onCancel]);

  if (!open) return null;

  const isDanger = variant === "danger";

  return (
    <div
      className="fixed inset-0 z-[9998] flex items-center justify-center bg-black/50 animate-in fade-in duration-200"
      onClick={onCancel}
    >
      <div
        className="mx-4 w-full max-w-md rounded-xl bg-white p-6 shadow-xl animate-in zoom-in-95 duration-200"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start gap-4">
          {isDanger && (
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-red-100">
              <AlertTriangle className="h-5 w-5 text-red-600" />
            </div>
          )}
          <div className="flex-1">
            <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            <p className="mt-1 text-sm text-gray-500">{description}</p>
          </div>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <Button
            type="button"
            variant="outline"
            onClick={onCancel}
            disabled={loading}
          >
            {cancelLabel}
          </Button>
          <Button
            type="button"
            variant={isDanger ? "destructive" : "default"}
            onClick={onConfirm}
            disabled={loading}
            className={cn(isDanger && "bg-red-600 hover:bg-red-700 text-white")}
          >
            {loading ? "İşleniyor..." : confirmLabel}
          </Button>
        </div>
      </div>
    </div>
  );
}
