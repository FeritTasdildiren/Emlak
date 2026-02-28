"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Building2,
  FileText,
  Users,
  Menu,
  X,
  TrendingUp,
  BarChart3,
  Map,
  MessageSquare,
  Store,
  Calculator,
  Settings,
  MoreHorizontal,
} from "lucide-react";
import { useState } from "react";

// --- Tüm navigasyon öğeleri (11 adet) ---
const allNavItems = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: Building2, label: "İlanlarım", href: "/properties" },
  { icon: FileText, label: "İlan Asistanı", href: "/listings" },
  { icon: Users, label: "Müşteriler", href: "/dashboard/customers" },
  { icon: TrendingUp, label: "Değerleme", href: "/valuations" },
  { icon: BarChart3, label: "Bölge Analizi", href: "/areas" },
  { icon: Map, label: "Harita", href: "/maps" },
  { icon: MessageSquare, label: "Mesajlar", href: "/messages" },
  { icon: Store, label: "Vitrinler", href: "/network" },
  { icon: Calculator, label: "Kredi", href: "/calculator" },
  { icon: Settings, label: "Ayarlar", href: "/settings" },
];

// Bottom tab bar'da gösterilecek 4 + "Daha Fazla" = 5 öğe
const bottomTabItems = allNavItems.slice(0, 4);
const moreMenuItems = allNavItems.slice(4);

export function MobileNav() {
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [isMoreOpen, setIsMoreOpen] = useState(false);
  const pathname = usePathname();

  const isActive = (href: string) =>
    pathname === href || pathname.startsWith(href + "/");

  return (
    <>
      {/* Üst Header (Hamburger + Logo) */}
      <div className="lg:hidden flex items-center p-4 border-b bg-white">
        <button
          onClick={() => setIsDrawerOpen(!isDrawerOpen)}
          className="p-2 -ml-2"
          aria-label="Menüyü aç"
        >
          <Menu className="w-6 h-6" />
        </button>
        <span className="font-bold text-lg ml-2">EmlakTech</span>
      </div>

      {/* Drawer Overlay (Hamburger menü) */}
      {isDrawerOpen && (
        <div
          className="fixed inset-0 z-50 bg-black/50 lg:hidden"
          onClick={() => setIsDrawerOpen(false)}
        >
          <div
            className="absolute left-0 top-0 bottom-0 w-72 bg-white p-4 shadow-xl animate-in slide-in-from-left duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-6">
              <span className="font-bold text-xl text-blue-600">
                EmlakTech
              </span>
              <button
                onClick={() => setIsDrawerOpen(false)}
                className="p-1.5 rounded-md hover:bg-gray-100"
                aria-label="Menüyü kapat"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <nav className="space-y-1">
              {allNavItems.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setIsDrawerOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 text-sm font-medium rounded-md transition-colors",
                    isActive(item.href)
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-700 hover:bg-gray-50"
                  )}
                >
                  <item.icon className="w-5 h-5" />
                  {item.label}
                </Link>
              ))}
            </nav>
          </div>
        </div>
      )}

      {/* Bottom Tab Bar (Mobil) */}
      <div className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-gray-200 safe-area-pb">
        <nav className="flex items-center justify-around px-2 py-1">
          {bottomTabItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center gap-0.5 px-2 py-1.5 min-w-[56px] rounded-md transition-colors",
                isActive(item.href)
                  ? "text-blue-600"
                  : "text-gray-500 hover:text-gray-700"
              )}
            >
              <item.icon className="w-5 h-5" />
              <span className="text-[10px] font-medium leading-tight">
                {item.label}
              </span>
            </Link>
          ))}

          {/* Daha Fazla (...) butonu */}
          <button
            onClick={() => setIsMoreOpen(!isMoreOpen)}
            className={cn(
              "flex flex-col items-center gap-0.5 px-2 py-1.5 min-w-[56px] rounded-md transition-colors",
              isMoreOpen ? "text-blue-600" : "text-gray-500 hover:text-gray-700"
            )}
          >
            <MoreHorizontal className="w-5 h-5" />
            <span className="text-[10px] font-medium leading-tight">
              Daha Fazla
            </span>
          </button>
        </nav>
      </div>

      {/* "Daha Fazla" Bottom Sheet */}
      {isMoreOpen && (
        <div
          className="lg:hidden fixed inset-0 z-50 bg-black/30"
          onClick={() => setIsMoreOpen(false)}
        >
          <div
            className="absolute bottom-0 left-0 right-0 bg-white rounded-t-2xl shadow-[0_-5px_20px_rgba(0,0,0,0.1)] animate-in slide-in-from-bottom duration-200"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Handle */}
            <div className="p-2 flex justify-center">
              <div className="w-12 h-1.5 bg-gray-300 rounded-full" />
            </div>

            <div className="px-4 pb-6 pt-2">
              <h3 className="text-sm font-semibold text-gray-500 uppercase tracking-wider mb-3">
                Diğer Sayfalar
              </h3>
              <div className="grid grid-cols-3 gap-3">
                {moreMenuItems.map((item) => (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setIsMoreOpen(false)}
                    className={cn(
                      "flex flex-col items-center gap-1.5 p-3 rounded-xl transition-colors",
                      isActive(item.href)
                        ? "bg-blue-50 text-blue-700"
                        : "bg-gray-50 text-gray-700 hover:bg-gray-100"
                    )}
                  >
                    <item.icon className="w-6 h-6" />
                    <span className="text-xs font-medium text-center leading-tight">
                      {item.label}
                    </span>
                  </Link>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
