"use client";

import { Home, Plus } from "lucide-react";

/**
 * Telegram Mini App - Listings (Portföy) Sayfası
 * 
 * TODO: useTgProperties() hook'u eklendiğinde API'den veri çekecek şekilde güncellenecek.
 */
export default function TGListingsPage() {
  return (
    <div className="flex flex-col items-center justify-center px-8 pt-20 text-center">
      <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-slate-100"
           style={{ backgroundColor: "var(--tg-theme-secondary-bg-color, #f1f5f9)" }}>
        <Home className="h-10 w-10 text-slate-300" 
              style={{ color: "var(--tg-theme-hint-color, #94a3b8)" }} />
      </div>
      <h2 className="mb-2 text-lg font-semibold text-slate-700"
          style={{ color: "var(--tg-theme-text-color, #334155)" }}>
        Henüz ilan yok
      </h2>
      <p className="mb-6 text-sm leading-relaxed text-slate-400"
         style={{ color: "var(--tg-theme-hint-color, #94a3b8)" }}>
        Portföyünüze yeni ilanlar ekleyerek başlayabilirsiniz.
      </p>
      <button
        type="button"
        className="flex items-center gap-2 rounded-xl bg-orange-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-orange-600/30 transition-all active:scale-95"
      >
        <Plus className="h-4 w-4" />
        Yeni İlan Ekle
      </button>
    </div>
  );
}
