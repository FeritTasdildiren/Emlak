"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { usePlan } from "@/hooks/use-plan";
import { FeatureKey } from "@/lib/plan-features";
import {
  LayoutDashboard,
  Building2,
  FileText,
  Users,
  Calculator,
  BarChart3,
  MessageSquare,
  Map,
  Network,
  Settings,
  Coins,
  Lock,
} from "lucide-react";

interface SidebarItem {
  icon: React.ElementType;
  label: string;
  href: string;
  feature?: FeatureKey;
}

const sidebarItems: SidebarItem[] = [
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: Building2, label: "İlanlarım", href: "/properties" },
  { icon: FileText, label: "İlan Asistanı", href: "/listings", feature: 'hasAiAssistant' },
  { icon: Users, label: "Müşteriler", href: "/dashboard/customers" },
  { icon: Calculator, label: "Değerleme", href: "/valuations" },
  { icon: BarChart3, label: "Bölge Analizi", href: "/areas" },
  { icon: MessageSquare, label: "Mesajlar", href: "/messages" },
  { icon: Map, label: "Harita", href: "/maps" },
  { icon: Network, label: "Paylaşım Ağı", href: "/network", feature: 'hasSharingNetwork' },
  { icon: Coins, label: "Kredi", href: "/calculator" },
  { icon: Settings, label: "Ayarlar", href: "/settings" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { checkAccess, plan } = usePlan();

  return (
    <aside className="hidden lg:flex flex-col w-64 border-r bg-white h-screen sticky top-0">
      <div className="p-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-blue-600">EmlakTech</h1>
        <div className="px-2 py-0.5 rounded bg-blue-100 text-blue-700 text-[10px] font-bold uppercase tracking-wider">
          {plan}
        </div>
      </div>
      <nav className="flex-1 px-4 space-y-1">
        {sidebarItems.map((item) => {
          const isActive = pathname === item.href || pathname.startsWith(item.href + "/");
          const hasAccess = item.feature ? checkAccess(item.feature) : true;

          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center justify-between px-3 py-2 text-sm font-medium rounded-md transition-colors",
                isActive
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-700 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <div className="flex items-center gap-3">
                <item.icon className="w-5 h-5" />
                {item.label}
              </div>
              {hasAccess === false && (
                <Lock className="w-3.5 h-3.5 text-amber-500" />
              )}
            </Link>
          );
        })}
      </nav>

      <div className="p-4 border-t">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-blue-600 font-bold text-xs">
            JD
          </div>
          <div className="flex flex-col">
            <span className="text-sm font-medium">John Doe</span>
            <span className="text-xs text-gray-500">Broker</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
