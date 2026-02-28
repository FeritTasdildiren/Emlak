"use client";

import type { ReactNode } from "react";
import { useTgAuth } from "@/app/tg/hooks/use-tg-auth";

// ================================================================
// Types
// ================================================================

interface TgAuthGuardProps {
  children: ReactNode;
}

// ================================================================
// Component
// ================================================================

/**
 * Telegram Mini App auth guard.
 *
 * - Authenticated değilse auth akışını otomatik başlatır (useTgAuth hook).
 * - Loading durumunda skeleton/spinner gösterir.
 * - Hata durumunda "Giriş yapılamadı" mesajı + yeniden dene butonu gösterir.
 * - Başarılı auth sonrası children render eder.
 */
export function TgAuthGuard({ children }: TgAuthGuardProps) {
  const { state, error, retry } = useTgAuth();

  // --- Loading ---
  if (state === "loading") {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="h-10 w-10 animate-spin rounded-full border-4 border-orange-200 border-t-orange-600" />
          <p className="text-sm text-gray-500">Giriş yapılıyor...</p>
        </div>
      </div>
    );
  }

  // --- Error ---
  if (state === "error") {
    return (
      <div className="flex min-h-[60vh] items-center justify-center px-6">
        <div className="max-w-sm rounded-2xl bg-white p-8 text-center shadow-lg">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-red-100">
            <svg
              className="h-7 w-7 text-red-600"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"
              />
            </svg>
          </div>
          <h3 className="mb-2 text-base font-bold text-gray-900">
            Giriş Yapılamadı
          </h3>
          <p className="mb-6 text-sm text-gray-500">
            {error || "Telegram üzerinden giriş yapılamadı. Lütfen tekrar deneyin."}
          </p>
          <button
            onClick={retry}
            type="button"
            className="w-full rounded-xl bg-orange-600 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-orange-700 active:bg-orange-800"
          >
            Tekrar Dene
          </button>
        </div>
      </div>
    );
  }

  // --- Authenticated ---
  return <>{children}</>;
}
