"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Calculator, Home, Settings, Users } from "lucide-react";
import { cn } from "@/lib/utils";

// ================================================================
// Types
// ================================================================

interface NavTab {
  icon: typeof Home;
  label: string;
  href: string;
}

// ================================================================
// Tab Konfigurasyonu
// ================================================================

const tabs: NavTab[] = [
  { icon: Home, label: "Ana Sayfa", href: "/tg" },
  { icon: Calculator, label: "Değerleme", href: "/tg/valuation" },
  { icon: Users, label: "CRM", href: "/tg/crm" },
  { icon: Settings, label: "Ayarlar", href: "/tg/settings" },
];

// ================================================================
// Component
// ================================================================

/**
 * Telegram Mini App alt navigasyon bari.
 *
 * - 4 sekme: Ana Sayfa, Değerleme, CRM, Ayarlar
 * - Aktif sekme orange-600 ile vurgulanir
 * - usePathname() ile aktif route tespit edilir
 * - Safe area padding (Telegram bottom inset)
 * - Lucide ikonlar
 */
export function TgBottomNav() {
  const pathname = usePathname();

  return (
    <nav
      className={cn(
        "fixed bottom-0 left-0 right-0 z-50",
        "bg-white/95 backdrop-blur-sm border-t border-gray-200",
        "flex items-center justify-around",
        "h-16 pb-[env(safe-area-inset-bottom,0px)]",
      )}
      style={{
        paddingBottom:
          "max(env(safe-area-inset-bottom, 0px), var(--tg-viewport-safe-area-inset-bottom, 0px))",
      }}
    >
      {tabs.map((tab) => {
        // Tam esleme: /tg icin sadece /tg, alt route'lar icin startsWith
        const isActive =
          tab.href === "/tg"
            ? pathname === "/tg"
            : pathname.startsWith(tab.href);

        return (
          <Link
            key={tab.href}
            href={tab.href}
            className={cn(
              "flex flex-col items-center justify-center",
              "w-full h-full gap-0.5",
              "transition-colors duration-150",
              isActive
                ? "text-orange-600"
                : "text-gray-400 active:text-gray-600",
            )}
          >
            <tab.icon
              className={cn("h-5 w-5", isActive && "stroke-[2.5]")}
            />
            <span
              className={cn(
                "text-[10px] leading-tight",
                isActive ? "font-semibold" : "font-medium",
              )}
            >
              {tab.label}
            </span>
          </Link>
        );
      })}
    </nav>
  );
}
