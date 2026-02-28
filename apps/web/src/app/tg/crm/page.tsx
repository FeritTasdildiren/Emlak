"use client";

import { useCallback, useMemo, useState } from "react";
import { SegmentedControl } from "@/app/tg/components/segmented-control";
import { TgSkeleton } from "@/app/tg/components/tg-skeleton";
import {
  useTgCustomers,
  useTgCreateCustomer,
  type LeadStatus,
} from "@/app/tg/hooks/use-tg-customers";
import type { ApiCustomer, CustomerCreateBody } from "@/app/tg/lib/tg-api";
import {
  AlertTriangle,
  Check,
  Phone,
  Plus,
  RefreshCw,
  Search,
  SlidersHorizontal,
  UserPlus,
  Users,
  Wallet,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ================================================================
// Types & Constants
// ================================================================

type CustomerType = "Alıcı" | "Satıcı" | "Kiracı" | "Ev Sahibi";

interface PipelineTab {
  label: string;
  status: LeadStatus | null;
}

const PIPELINE_TABS: PipelineTab[] = [
  { label: "Tümü", status: null },
  { label: "Yeni", status: "cold" },
  { label: "İletişimde", status: "warm" },
  { label: "Görüştü", status: "hot" },
  { label: "Kapandı", status: "converted" },
];

const CUSTOMER_TYPE_MAP: Record<CustomerType, ApiCustomer["customer_type"]> = {
  Alıcı: "buyer",
  Satıcı: "seller",
  Kiracı: "renter",
  "Ev Sahibi": "landlord",
};

const CUSTOMER_TYPE_REVERSE: Record<string, CustomerType> = {
  buyer: "Alıcı",
  seller: "Satıcı",
  renter: "Kiracı",
  landlord: "Ev Sahibi",
};

const CUSTOMER_TYPE_STYLES: Record<CustomerType, { bg: string; text: string }> = {
  Alıcı: { bg: "bg-blue-50", text: "text-blue-700" },
  Satıcı: { bg: "bg-emerald-50", text: "text-emerald-700" },
  Kiracı: { bg: "bg-amber-50", text: "text-amber-700" },
  "Ev Sahibi": { bg: "bg-purple-50", text: "text-purple-700" },
};

const CUSTOMER_TYPES: CustomerType[] = [
  "Alıcı",
  "Satıcı",
  "Kiracı",
  "Ev Sahibi",
];

const AVATAR_COLORS = [
  { bg: "bg-blue-100", text: "text-blue-700" },
  { bg: "bg-emerald-100", text: "text-emerald-700" },
  { bg: "bg-amber-100", text: "text-amber-700" },
  { bg: "bg-purple-100", text: "text-purple-700" },
  { bg: "bg-rose-100", text: "text-rose-700" },
];

// ================================================================
// CRM Page
// ================================================================

export default function TGCRMPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState<LeadStatus | null>(null);
  const [showModal, setShowModal] = useState(false);

  // Debounced search would be ideal, but for simplicity we filter client-side
  // after fetching. The API also supports ?search= for server-side search.
  const {
    customers: apiCustomers,
    total,
    isLoading,
    isError,
    error,
    refetch,
  } = useTgCustomers({
    page: 1,
    perPage: 50,
    leadStatus: activeTab,
  });

  // Client-side search filtering (instant UI feedback)
  const filteredCustomers = useMemo(() => {
    if (!searchQuery) return apiCustomers;
    const q = searchQuery.toLowerCase();
    return apiCustomers.filter(
      (c) =>
        c.full_name.toLowerCase().includes(q) ||
        (c.phone && c.phone.includes(q)) ||
        (c.tags && c.tags.some((t) => t.toLowerCase().includes(q))),
    );
  }, [apiCustomers, searchQuery]);

  const getInitials = (name: string) =>
    name
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);

  const getAvatarColor = (name: string) => {
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    return AVATAR_COLORS[Math.abs(hash) % AVATAR_COLORS.length];
  };

  const openModal = useCallback(() => setShowModal(true), []);
  const closeModal = useCallback(() => setShowModal(false), []);

  // --- Loading State ---
  if (isLoading) {
    return <CrmSkeleton />;
  }

  // --- Error State ---
  if (isError) {
    return <CrmError message={error} onRetry={() => refetch()} />;
  }

  // --- Empty State ---
  if (total === 0 && !searchQuery && !activeTab) {
    return (
      <>
        <CrmEmpty onAdd={openModal} />
        {showModal && (
          <AddCustomerBottomSheet onClose={closeModal} />
        )}
      </>
    );
  }

  // --- Filled State ---
  return (
    <>
      <div className="space-y-2 pb-4">
        {/* Search Bar */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
            <input
              type="text"
              placeholder="Müşteri ara..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full min-h-[44px] rounded-xl border border-slate-200 bg-white py-2.5 pl-10 pr-4 text-sm focus:border-orange-500 focus:ring-2 focus:ring-orange-500 focus:outline-none"
            />
          </div>
          <button
            type="button"
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border border-slate-200 bg-white"
          >
            <SlidersHorizontal className="h-4 w-4 text-slate-500" />
          </button>
        </div>

        {/* Pipeline Tabs */}
        <div className="flex gap-1 overflow-x-auto [-ms-overflow-style:none] [scrollbar-width:none] [-webkit-overflow-scrolling:touch] [&::-webkit-scrollbar]:hidden py-1">
          {PIPELINE_TABS.map((tab) => {
            const isActive = tab.status === activeTab;
            return (
              <button
                key={tab.label}
                type="button"
                onClick={() => setActiveTab(tab.status)}
                className={cn(
                  "flex shrink-0 items-center gap-1.5 rounded-full px-4 py-2 text-[13px] font-medium transition-all min-h-[36px]",
                  isActive
                    ? "bg-orange-600 text-white"
                    : "bg-slate-100 text-slate-500",
                )}
                style={
                  !isActive
                    ? {
                        backgroundColor:
                          "var(--tg-theme-secondary-bg-color, #f1f5f9)",
                        color: "var(--tg-theme-hint-color, #64748b)",
                      }
                    : undefined
                }
              >
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Customer List */}
        <div className="space-y-2">
          {filteredCustomers.length === 0 ? (
            <div className="py-12 text-center">
              <p className="text-sm text-slate-400">Sonuç bulunamadı</p>
            </div>
          ) : (
            filteredCustomers.map((customer) => (
              <CustomerCard
                key={customer.id}
                customer={customer}
                getInitials={getInitials}
                getAvatarColor={getAvatarColor}
              />
            ))
          )}
        </div>
      </div>

      {/* FAB */}
      <button
        type="button"
        onClick={openModal}
        className="fixed bottom-24 right-4 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-orange-600 text-white shadow-lg shadow-orange-600/30 transition-all active:scale-90"
      >
        <Plus className="h-6 w-6" />
      </button>

      {/* Bottom Sheet Modal */}
      {showModal && (
        <AddCustomerBottomSheet onClose={closeModal} />
      )}
    </>
  );
}

// ================================================================
// Customer Card
// ================================================================

function CustomerCard({
  customer,
  getInitials,
  getAvatarColor,
}: {
  customer: ApiCustomer;
  getInitials: (name: string) => string;
  getAvatarColor: (name: string) => { bg: string; text: string };
}) {
  const typeLabel = CUSTOMER_TYPE_REVERSE[customer.customer_type] ?? "Alıcı";
  const typeStyle = CUSTOMER_TYPE_STYLES[typeLabel];
  const avatarColor = getAvatarColor(customer.full_name);

  const formatBudget = (n: number | null) => {
    if (!n) return "—";
    if (n >= 1_000_000) return `₺${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `₺${(n / 1_000).toFixed(0)}K`;
    return `₺${n}`;
  };

  const timeAgo = useMemo(() => {
    const date = new Date(customer.created_at);
    const now = Date.now();
    const diff = now - date.getTime();
    const mins = Math.floor(diff / 60_000);
    if (mins < 60) return `${mins}dk önce`;
    const hours = Math.floor(mins / 60);
    if (hours < 24) return `${hours}sa önce`;
    const days = Math.floor(hours / 24);
    if (days < 7) return `${days} gün önce`;
    return `${Math.floor(days / 7)} hafta önce`;
  }, [customer.created_at]);

  return (
    <div className="rounded-2xl bg-white p-3.5 shadow-sm">
      <div className="flex items-start gap-3">
        {/* Avatar */}
        <div
          className={cn(
            "flex h-10 w-10 shrink-0 items-center justify-center rounded-full",
            avatarColor.bg,
          )}
        >
          <span className={cn("text-sm font-bold", avatarColor.text)}>
            {getInitials(customer.full_name)}
          </span>
        </div>

        {/* Content */}
        <div className="min-w-0 flex-1">
          {/* Name + Type Badge */}
          <div className="flex items-center justify-between">
            <h3 className="truncate text-sm font-semibold">{customer.full_name}</h3>
            <span
              className={cn(
                "shrink-0 rounded-full px-2 py-0.5 text-[11px] font-medium",
                typeStyle.bg,
                typeStyle.text,
              )}
            >
              {typeLabel}
            </span>
          </div>

          {/* Phone */}
          {customer.phone && (
            <a
              href={`tel:${customer.phone.replace(/\s/g, "")}`}
              className="mt-0.5 flex items-center gap-1 text-xs text-slate-400"
            >
              <Phone className="h-3 w-3" />
              {customer.phone}
            </a>
          )}

          {/* Budget + Time */}
          <div className="mt-2 flex items-center justify-between">
            <div className="flex items-center gap-1 text-xs text-slate-500">
              <Wallet className="h-3 w-3" />
              <span className="font-mono">
                {formatBudget(customer.budget_min)} — {formatBudget(customer.budget_max)}
              </span>
            </div>
            <span className="text-[10px] text-slate-400">{timeAgo}</span>
          </div>

          {/* Tags */}
          {customer.tags && customer.tags.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {customer.tags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] text-slate-600"
                >
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ================================================================
// Add Customer Bottom Sheet
// ================================================================

function AddCustomerBottomSheet({ onClose }: { onClose: () => void }) {
  const { create, isPending, isError, error, reset } = useTgCreateCustomer();

  const [newName, setNewName] = useState("");
  const [newPhone, setNewPhone] = useState("");
  const [newType, setNewType] = useState<string>("Alıcı");
  const [newBudgetMin, setNewBudgetMin] = useState("");
  const [newBudgetMax, setNewBudgetMax] = useState("");

  const handleSave = useCallback(() => {
    if (!newName.trim()) return;

    const body: CustomerCreateBody = {
      full_name: newName.trim(),
      phone: newPhone.trim() || undefined,
      customer_type: CUSTOMER_TYPE_MAP[newType as CustomerType] ?? "buyer",
      budget_min: newBudgetMin ? Number(newBudgetMin) * 1_000_000 : undefined,
      budget_max: newBudgetMax ? Number(newBudgetMax) * 1_000_000 : undefined,
      source: "telegram_mini_app",
    };

    create(body, {
      onSuccess: () => {
        onClose();
      },
    });
  }, [newName, newPhone, newType, newBudgetMin, newBudgetMax, create, onClose]);

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50 bg-black/40 backdrop-blur-sm"
        onClick={onClose}
        onKeyDown={(e) => {
          if (e.key === "Escape") onClose();
        }}
        role="button"
        tabIndex={0}
        aria-label="Kapat"
      />

      {/* Sheet */}
      <div className="fixed bottom-0 left-0 right-0 z-50 max-h-[85dvh] overflow-y-auto rounded-t-3xl bg-white">
        {/* Drag indicator */}
        <div className="flex justify-center pb-2 pt-3">
          <div className="h-1 w-10 rounded-full bg-slate-300" />
        </div>

        <div className="px-5 pb-6">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-bold">Hızlı Müşteri Kayıt</h2>
            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-100"
            >
              <X className="h-4 w-4 text-slate-500" />
            </button>
          </div>

          {/* Error message */}
          {isError && (
            <div className="mb-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">
              {error ?? "Kayıt sırasında bir hata oluştu."}
              <button
                type="button"
                onClick={reset}
                className="ml-2 text-xs font-semibold underline"
              >
                Kapat
              </button>
            </div>
          )}

          {/* Ad Soyad */}
          <div className="mb-4">
            <label className="mb-1.5 block text-sm font-medium">
              Ad Soyad
            </label>
            <input
              type="text"
              placeholder="Müşteri adı..."
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full min-h-[44px] rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm focus:border-orange-500 focus:ring-2 focus:ring-orange-500 focus:outline-none"
            />
          </div>

          {/* Telefon */}
          <div className="mb-4">
            <label className="mb-1.5 block text-sm font-medium">Telefon</label>
            <input
              type="tel"
              placeholder="05XX XXX XX XX"
              value={newPhone}
              onChange={(e) => setNewPhone(e.target.value)}
              className="w-full min-h-[44px] rounded-xl border border-slate-200 bg-white px-4 py-3 font-mono text-sm focus:border-orange-500 focus:ring-2 focus:ring-orange-500 focus:outline-none"
            />
          </div>

          {/* Tip */}
          <div className="mb-4">
            <label className="mb-1.5 block text-sm font-medium">
              Müşteri Tipi
            </label>
            <SegmentedControl
              options={CUSTOMER_TYPES}
              value={newType}
              onChange={setNewType}
            />
          </div>

          {/* Bütçe */}
          <div className="mb-5">
            <label className="mb-1.5 block text-sm font-medium">
              Bütçe Aralığı (Milyon ₺)
            </label>
            <div className="flex items-center gap-2">
              <div className="relative flex-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">
                  ₺
                </span>
                <input
                  type="text"
                  placeholder="Min"
                  value={newBudgetMin}
                  onChange={(e) => setNewBudgetMin(e.target.value)}
                  className="w-full min-h-[44px] rounded-xl border border-slate-200 bg-white py-3 pl-8 pr-3 font-mono text-sm focus:border-orange-500 focus:ring-2 focus:ring-orange-500 focus:outline-none"
                />
              </div>
              <span className="text-sm text-slate-400">—</span>
              <div className="relative flex-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm text-slate-400">
                  ₺
                </span>
                <input
                  type="text"
                  placeholder="Max"
                  value={newBudgetMax}
                  onChange={(e) => setNewBudgetMax(e.target.value)}
                  className="w-full min-h-[44px] rounded-xl border border-slate-200 bg-white py-3 pl-8 pr-3 font-mono text-sm focus:border-orange-500 focus:ring-2 focus:ring-orange-500 focus:outline-none"
                />
              </div>
            </div>
          </div>

          {/* Save Button */}
          <button
            type="button"
            onClick={handleSave}
            disabled={!newName.trim() || isPending}
            className={cn(
              "flex w-full min-h-[48px] items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-semibold text-white shadow-lg shadow-orange-600/20 transition-all active:scale-[0.98]",
              newName.trim() && !isPending
                ? "bg-orange-600 hover:bg-orange-700"
                : "cursor-not-allowed bg-slate-300",
            )}
          >
            {isPending ? (
              <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
            ) : (
              <Check className="h-4 w-4" />
            )}
            {isPending ? "Kaydediliyor..." : "Müşteriyi Kaydet"}
          </button>
        </div>
      </div>
    </>
  );
}

// ================================================================
// Error State
// ================================================================

function CrmError({
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
        Müşteriler yüklenemedi
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
// Skeleton
// ================================================================

function CrmSkeleton() {
  return (
    <div className="space-y-3 pb-4">
      <TgSkeleton className="h-11 rounded-xl" />
      <div className="flex gap-2">
        <TgSkeleton className="h-9 w-20 rounded-full" />
        <TgSkeleton className="h-9 w-24 rounded-full" />
        <TgSkeleton className="h-9 w-20 rounded-full" />
        <TgSkeleton className="h-9 w-16 rounded-full" />
      </div>
      <TgSkeleton className="h-32 rounded-2xl" />
      <TgSkeleton className="h-32 rounded-2xl" />
      <TgSkeleton className="h-32 rounded-2xl" />
      <TgSkeleton className="h-32 rounded-2xl" />
    </div>
  );
}

// ================================================================
// Empty State
// ================================================================

function CrmEmpty({ onAdd }: { onAdd: () => void }) {
  return (
    <>
      <div className="flex flex-col items-center justify-center px-8 pt-20 text-center">
        <div className="mb-4 flex h-20 w-20 items-center justify-center rounded-full bg-slate-100">
          <Users className="h-10 w-10 text-slate-300" />
        </div>
        <h2 className="mb-2 text-lg font-semibold text-slate-700">
          Henüz müşteri yok
        </h2>
        <p className="mb-6 text-sm leading-relaxed text-slate-400">
          Sağ alttaki + butonuna tıklayarak ilk müşterinizi ekleyebilirsiniz.
        </p>
        <button
          type="button"
          onClick={onAdd}
          className="flex items-center gap-2 rounded-xl bg-orange-600 px-6 py-3 text-sm font-semibold text-white"
        >
          <UserPlus className="h-4 w-4" />
          İlk Müşteriyi Ekle
        </button>
      </div>

      {/* FAB */}
      <button
        type="button"
        onClick={onAdd}
        className="fixed bottom-24 right-4 z-40 flex h-14 w-14 items-center justify-center rounded-full bg-orange-600 text-white shadow-lg shadow-orange-600/30 transition-all active:scale-90"
      >
        <Plus className="h-6 w-6" />
      </button>
    </>
  );
}
