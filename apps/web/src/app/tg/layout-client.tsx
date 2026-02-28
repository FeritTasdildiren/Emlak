"use client";

import type { ReactNode } from "react";
import { TgProvider } from "@/app/tg/components/tg-provider";
import { TgAuthGuard } from "@/app/tg/components/tg-auth-guard";
import { TgBottomNav } from "@/app/tg/components/tg-bottom-nav";

// ================================================================
// Mini App Root Layout
// ================================================================

/**
 * Telegram Mini App root layout.
 *
 * Tasarım kararları:
 * - Üst bar YOK: Telegram kendi üst barını sağlıyor.
 * - Alt navigasyon barı: 4 sekme (Ana Sayfa, Değerleme, CRM, Ayarlar).
 * - TgProvider: SDK init, viewport expand, tema CSS variables.
 * - TgAuthGuard: initData → JWT auth akışı.
 * - Tema: Telegram tema renkleri CSS variable olarak kullanılır.
 * - Mobil optimize: 375px min genişlik, safe area padding.
 *
 * Katman sırası:
 *   TgProvider → TgAuthGuard → Content + TgBottomNav
 */
export default function TGLayout({ children }: { children: ReactNode }) {
  return (
    <TgProvider>
      <TgAuthGuard>
        <div
          className="flex min-h-screen flex-col text-gray-900"
          style={{
            backgroundColor: "var(--tg-theme-bg-color, #f9fafb)",
            color: "var(--tg-theme-text-color, #111827)",
            minWidth: 375,
          }}
        >
          {/* Main Content — bottom nav'a alan birak */}
          <main className="flex-1 overflow-y-auto px-4 pb-20 pt-2">
            {children}
          </main>

          {/* Bottom Navigation */}
          <TgBottomNav />
        </div>
      </TgAuthGuard>
    </TgProvider>
  );
}
