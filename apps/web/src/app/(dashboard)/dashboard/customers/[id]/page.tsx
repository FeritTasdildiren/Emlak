"use client";

import { useState, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  Phone,
  Mail,
  Calendar,
  User,
  FileText,
  Home,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { CustomerInfo } from "@/components/customers/customer-info";
import { CustomerNotes } from "@/components/customers/customer-notes";
import { MatchList } from "@/components/customers/match-list";
import { useCustomerDetail } from "@/hooks/use-customer-detail";
import type { CustomerType, LeadStatus } from "@/types/customer";
import { cn } from "@/lib/utils";

// --- Konfigürasyon ---

type TabId = "info" | "notes" | "matches";

const TABS: { id: TabId; label: string; icon: typeof User }[] = [
  { id: "info", label: "Bilgiler", icon: User },
  { id: "notes", label: "Notlar", icon: FileText },
  { id: "matches", label: "Eşleşmeler", icon: Home },
];

const LEAD_STATUS_CONFIG: Record<
  LeadStatus,
  { label: string; className: string }
> = {
  cold: { label: "Soğuk", className: "bg-gray-100 text-gray-800" },
  warm: { label: "Ilık", className: "bg-yellow-100 text-yellow-800" },
  hot: { label: "Sıcak", className: "bg-red-100 text-red-800" },
  converted: {
    label: "Dönüşüm",
    className: "bg-emerald-100 text-emerald-800",
  },
  lost: { label: "Kayıp", className: "bg-slate-100 text-slate-600" },
};

const CUSTOMER_TYPE_CONFIG: Record<
  CustomerType,
  { label: string; className: string }
> = {
  buyer: { label: "Alıcı", className: "bg-indigo-100 text-indigo-800" },
  seller: { label: "Satıcı", className: "bg-amber-100 text-amber-800" },
  renter: { label: "Kiracı", className: "bg-violet-100 text-violet-800" },
  landlord: { label: "Ev Sahibi", className: "bg-teal-100 text-teal-800" },
};

// --- Yardımcı ---

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

function getRelativeTime(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);

  if (diffMin < 1) return "az önce";
  if (diffMin < 60) return `${diffMin} dk önce`;
  if (diffHour < 24) return `${diffHour} saat önce`;
  if (diffDay < 30) return `${diffDay} gün önce`;
  return new Intl.DateTimeFormat("tr-TR", {
    day: "numeric",
    month: "short",
  }).format(date);
}

// --- Sayfa ---

export default function CustomerDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = params.id as string;

  const [activeTab, setActiveTab] = useState<TabId>("info");
  const { customer, notes, matches } = useCustomerDetail(id);

  // Eşleştirme aksiyonları (şimdilik console.log — API sonra)
  const handleInterested = useCallback((matchId: string) => {
    console.log("İlgileniyorum:", matchId);
  }, []);

  const handlePassed = useCallback((matchId: string) => {
    console.log("Geçildi:", matchId);
  }, []);

  // Not ekleme (şimdilik console.log — API sonra)
  const handleAddNote = useCallback(
    (content: string, type: string) => {
      console.log("Yeni not:", { content, type, customer_id: id });
    },
    [id]
  );

  // 404 — Müşteri bulunamadı
  if (!customer) {
    return (
      <div className="px-4 sm:px-6 lg:px-8 py-8 w-full max-w-5xl mx-auto">
        <div className="text-center py-20">
          <User className="h-16 w-16 mx-auto mb-4 text-gray-300" />
          <h2 className="text-xl font-bold text-gray-900 mb-2">
            Müşteri Bulunamadı
          </h2>
          <p className="text-gray-500 mb-6">
            Aradığınız müşteri kaydı mevcut değil veya silinmiş olabilir.
          </p>
          <Button
            variant="outline"
            onClick={() => router.push("/dashboard/customers")}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Müşterilere Dön
          </Button>
        </div>
      </div>
    );
  }

  const statusConfig = LEAD_STATUS_CONFIG[customer.lead_status];
  const typeConfig = CUSTOMER_TYPE_CONFIG[customer.customer_type];
  const lastContact = customer.last_contact_at || customer.updated_at;

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 w-full max-w-5xl mx-auto space-y-6">
      {/* Breadcrumb + Geri Butonu */}
      <nav className="flex items-center gap-2" aria-label="Breadcrumb">
        <button
          onClick={() => router.push("/dashboard/customers")}
          className="inline-flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-700 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Müşteriler
        </button>
        <span className="text-gray-300">/</span>
        <span className="text-sm font-medium text-gray-900">
          {customer.full_name}
        </span>
      </nav>

      {/* Müşteri Başlık Kartı */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="p-6">
          <div className="sm:flex sm:items-center sm:justify-between">
            {/* Sol: Avatar + Ad + İletişim */}
            <div className="sm:flex sm:items-center">
              <div className="mb-4 sm:mb-0 sm:mr-6">
                <div className="h-20 w-20 rounded-full bg-blue-500 flex items-center justify-center text-white text-2xl font-bold border-4 border-white shadow-sm">
                  {getInitials(customer.full_name)}
                </div>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {customer.full_name}
                </h1>
                <div className="mt-1 flex flex-col sm:flex-row sm:flex-wrap sm:space-x-6">
                  {customer.phone && (
                    <div className="mt-2 flex items-center text-sm text-gray-500">
                      <Phone className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" />
                      {customer.phone}
                    </div>
                  )}
                  {customer.email && (
                    <div className="mt-2 flex items-center text-sm text-gray-500">
                      <Mail className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" />
                      {customer.email}
                    </div>
                  )}
                  <div className="mt-2 flex items-center text-sm text-gray-500">
                    <Calendar className="flex-shrink-0 mr-1.5 h-4 w-4 text-gray-400" />
                    Son iletişim: {getRelativeTime(lastContact)}
                  </div>
                </div>
              </div>
            </div>

            {/* Sağ: Badge'ler */}
            <div className="mt-5 flex items-center gap-2 sm:mt-0">
              <span
                className={cn(
                  "inline-flex items-center px-3 py-1 rounded-full text-sm font-medium",
                  typeConfig.className
                )}
              >
                {typeConfig.label}
              </span>
              <span
                className={cn(
                  "inline-flex items-center px-3 py-1 rounded-full text-sm font-medium",
                  statusConfig.className
                )}
              >
                {statusConfig.label}
              </span>
            </div>
          </div>
        </div>

        {/* Etiketler Footer */}
        {customer.tags.length > 0 && (
          <div className="bg-gray-50 px-6 py-3 flex flex-wrap gap-2 border-t border-gray-200">
            {customer.tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-white border border-gray-300 text-gray-700"
              >
                {tag}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Tabs */}
      <div className="bg-white shadow rounded-lg min-h-[500px]">
        {/* Tab Header */}
        <div className="border-b border-gray-200">
          <nav className="-mb-px flex space-x-8 px-6" aria-label="Tabs">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;

              // Not ve eşleşme sayıları
              let count: number | null = null;
              if (tab.id === "notes") count = notes.length;
              if (tab.id === "matches") count = matches.length;

              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={cn(
                    "whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors",
                    isActive
                      ? "border-blue-500 text-blue-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                  {count !== null && count > 0 && (
                    <span
                      className={cn(
                        "py-0.5 px-2 rounded-full text-xs ml-1",
                        isActive
                          ? "bg-blue-100 text-blue-600"
                          : "bg-gray-100 text-gray-600"
                      )}
                    >
                      {count}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab İçerikleri */}
        <div className="p-6">
          {activeTab === "info" && <CustomerInfo customer={customer} />}

          {activeTab === "notes" && (
            <CustomerNotes notes={notes} onAddNote={handleAddNote} />
          )}

          {activeTab === "matches" && (
            <MatchList
              matches={matches}
              onInterested={handleInterested}
              onPassed={handlePassed}
            />
          )}
        </div>
      </div>
    </div>
  );
}
