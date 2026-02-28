"use client";

import Link from "next/link";
import { useTgAuth } from "@/app/tg/hooks/use-tg-auth";
import { useTgDashboard } from "@/app/tg/hooks/use-tg-dashboard";
import { TgSkeleton } from "@/app/tg/components/tg-skeleton";
import {
  AlertTriangle,
  Building2,
  Calculator,
  Home,
  Inbox,
  Plus,
  RefreshCw,
  Shuffle,
  TrendingUp,
  UserPlus,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ================================================================
// Types
// ================================================================

interface MetricData {
  icon: typeof Home;
  label: string;
  value: number;
  subtitle: string;
  iconBg: string;
  iconColor: string;
  /** Quota bar (only for degerleme) */
  quota?: { used: number; total: number };
  /** Ping badge (only for eslesmeler) */
  ping?: number;
}

// ================================================================
// Dashboard Page
// ================================================================

export default function TGDashboardPage() {
  const { user } = useTgAuth();
  const { data, isLoading, isError, error, refetch } = useTgDashboard();

  const firstName = user?.full_name?.split(" ")[0] ?? "Kullanıcı";
  const initials =
    user?.full_name
      ?.split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2) ?? "KU";

  // --- Loading State ---
  if (isLoading) {
    return <DashboardSkeleton />;
  }

  // --- Error State ---
  if (isError) {
    return <DashboardError message={error} onRetry={() => refetch()} />;
  }

  // --- Empty State ---
  if (
    data &&
    data.propertyCount === 0 &&
    data.customerCount === 0 &&
    data.matchCount === 0
  ) {
    return <DashboardEmpty />;
  }

  // --- Build metrics from API data ---
  const metrics: MetricData[] = data
    ? [
        {
          icon: Home,
          label: "Portföy",
          value: data.propertyCount,
          subtitle: "Aktif ilan",
          iconBg: "bg-blue-50",
          iconColor: "text-blue-600",
        },
        {
          icon: Users,
          label: "Müşteriler",
          value: data.customerCount,
          subtitle: "Toplam kayıt",
          iconBg: "bg-emerald-50",
          iconColor: "text-emerald-600",
        },
        {
          icon: Shuffle,
          label: "Eşleşmeler",
          value: data.matchCount,
          subtitle: "Toplam eşleşme",
          iconBg: "bg-amber-50",
          iconColor: "text-amber-600",
          ping: data.matchCount > 0 ? data.matchCount : undefined,
        },
        {
          icon: Calculator,
          label: "Değerleme",
          value: data.credit.credit_balance,
          subtitle: "",
          iconBg: "bg-purple-50",
          iconColor: "text-purple-600",
          quota: {
            used:
              data.credit.credit_balance >= 0 ? data.credit.credit_balance : 0,
            total: 30,
          },
        },
      ]
    : [];

  // --- Filled State ---
  return (
    <div className="space-y-3 pb-4">
      {/* Welcome Card */}
      <div className="rounded-2xl bg-gradient-to-br from-orange-500 to-orange-700 p-4 text-white shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-white/80">Hoş geldin</p>
            <h1 className="mt-0.5 text-xl font-bold">{firstName}!</h1>
            <p className="mt-1 flex items-center gap-1 text-sm text-white/70">
              <Building2 className="h-3.5 w-3.5" />
              {data?.credit.plan_type ?? "Standart"} Plan
            </p>
          </div>
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-white/20">
            <span className="text-xl font-bold">{initials}</span>
          </div>
        </div>
      </div>

      {/* 2×2 Metric Cards */}
      <div className="grid grid-cols-2 gap-3">
        {metrics.map((metric) => (
          <MetricCard key={metric.label} data={metric} />
        ))}
      </div>

      {/* Quick Actions */}
      <div className="flex gap-3">
        <Link
          href="/tg/crm"
          className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-orange-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition-all active:scale-[0.98]"
        >
          <UserPlus className="h-4 w-4" />
          Yeni Müşteri
        </Link>
        <Link
          href="/tg/valuation"
          className="flex flex-1 items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-semibold text-slate-700 shadow-sm transition-all active:scale-[0.98]"
        >
          <Calculator className="h-4 w-4" />
          Değerleme Yap
        </Link>
      </div>
    </div>
  );
}

// ================================================================
// Sub-components
// ================================================================

function MetricCard({ data }: { data: MetricData }) {
  const Icon = data.icon;

  return (
    <div className="rounded-2xl bg-white p-4 shadow-sm">
      <div className="mb-2 flex items-center justify-between">
        <div
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-xl",
            data.iconBg,
          )}
        >
          <Icon className={cn("h-[18px] w-[18px]", data.iconColor)} />
        </div>
        {data.ping ? (
          <span className="relative flex h-5 w-5">
            <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-rose-400 opacity-75" />
            <span className="relative inline-flex h-5 w-5 items-center justify-center rounded-full bg-rose-500 text-[10px] font-bold text-white">
              {data.ping}
            </span>
          </span>
        ) : (
          <TrendingUp className="h-3 w-3 text-emerald-500" />
        )}
      </div>
      <p className="text-xs text-slate-500">{data.label}</p>
      <p className="mt-0.5 font-mono text-2xl font-bold">{data.value}</p>
      {data.quota ? (
        <div className="mt-1.5 flex items-center gap-2">
          <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100">
            <div
              className="h-full rounded-full bg-purple-500"
              style={{
                width: `${Math.min((data.quota.used / data.quota.total) * 100, 100)}%`,
              }}
            />
          </div>
          <span className="font-mono text-[10px] text-slate-400">
            {data.quota.used}/{data.quota.total}
          </span>
        </div>
      ) : (
        <p className="mt-0.5 text-[11px] text-slate-400">{data.subtitle}</p>
      )}
    </div>
  );
}

// ================================================================
// Error State
// ================================================================

function DashboardError({
  message,
  onRetry,
}: {
  message: string | null;
  onRetry: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center px-8 pt-20 text-center">
      <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-rose-50">
        <AlertTriangle className="h-10 w-10 text-rose-400" />
      </div>
      <h2 className="mb-2 text-lg font-semibold text-slate-700">
        Veriler yüklenemedi
      </h2>
      <p className="mb-6 text-sm text-slate-400">
        {message ?? "Bilinmeyen bir hata oluştu."}
      </p>
      <button
        type="button"
        onClick={onRetry}
        className="flex items-center gap-2 rounded-xl bg-orange-600 px-6 py-3 text-sm font-semibold text-white"
      >
        <RefreshCw className="h-4 w-4" />
        Tekrar Dene
      </button>
    </div>
  );
}

// ================================================================
// Loading Skeleton
// ================================================================

function DashboardSkeleton() {
  return (
    <div className="space-y-3 pb-4">
      {/* Welcome skeleton */}
      <TgSkeleton className="h-24 rounded-2xl" />
      {/* Card skeletons */}
      <div className="grid grid-cols-2 gap-3">
        <TgSkeleton className="h-32 rounded-2xl" />
        <TgSkeleton className="h-32 rounded-2xl" />
        <TgSkeleton className="h-32 rounded-2xl" />
        <TgSkeleton className="h-32 rounded-2xl" />
      </div>
      {/* Button skeletons */}
      <div className="flex gap-3">
        <TgSkeleton className="h-12 flex-1 rounded-xl" />
        <TgSkeleton className="h-12 flex-1 rounded-xl" />
      </div>
    </div>
  );
}

// ================================================================
// Empty State
// ================================================================

function DashboardEmpty() {
  return (
    <div className="flex flex-col items-center justify-center px-8 pt-20 text-center">
      <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-slate-100">
        <Inbox className="h-10 w-10 text-slate-300" />
      </div>
      <h2 className="mb-2 text-lg font-semibold text-slate-700">
        Henüz veri yok
      </h2>
      <p className="mb-6 text-sm text-slate-400">
        İlk müşterinizi ekleyerek veya değerleme yaparak başlayabilirsiniz.
      </p>
      <Link
        href="/tg/crm"
        className="flex items-center gap-2 rounded-xl bg-orange-600 px-6 py-3 text-sm font-semibold text-white"
      >
        <Plus className="h-4 w-4" />
        Başlayın
      </Link>
    </div>
  );
}
