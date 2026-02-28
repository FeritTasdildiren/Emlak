"use client";

import type { Customer, CustomerType, LeadStatus } from "@/types/customer";
import { cn } from "@/lib/utils";

// --- Konfigürasyon sabitleri ---

const LEAD_STATUS_CONFIG: Record<LeadStatus, { label: string; className: string }> = {
  cold: { label: "Soğuk", className: "bg-gray-100 text-gray-800" },
  warm: { label: "Ilık", className: "bg-yellow-100 text-yellow-800" },
  hot: { label: "Sıcak", className: "bg-red-100 text-red-800" },
  converted: { label: "Dönüşüm", className: "bg-emerald-100 text-emerald-800" },
  lost: { label: "Kayıp", className: "bg-slate-100 text-slate-600" },
};

const CUSTOMER_TYPE_CONFIG: Record<CustomerType, { label: string; className: string }> = {
  buyer: { label: "Alıcı", className: "bg-indigo-100 text-indigo-800" },
  seller: { label: "Satıcı", className: "bg-amber-100 text-amber-800" },
  renter: { label: "Kiracı", className: "bg-violet-100 text-violet-800" },
  landlord: { label: "Ev Sahibi", className: "bg-teal-100 text-teal-800" },
};

const SOURCE_LABELS: Record<string, string> = {
  web: "Web Sitesi",
  referral: "Referans",
  manual: "Manuel Giriş",
  whatsapp: "WhatsApp",
  telegram: "Telegram",
};

// --- Yardımcı fonksiyonlar ---

/** TL para birimi formatı: ₺1.500.000 */
function formatCurrencyTR(amount: number): string {
  return new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency: "TRY",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/** Bütçe aralığı formatı */
function formatBudgetRange(min?: number, max?: number): string {
  if (!min && !max) return "Belirtilmemiş";
  if (min && max) return `${formatCurrencyTR(min)} - ${formatCurrencyTR(max)}`;
  if (min) return `${formatCurrencyTR(min)}+`;
  if (max) return `${formatCurrencyTR(max)}'e kadar`;
  return "Belirtilmemiş";
}

/** Tarihi insan-okunur formata çevir */
function formatDateTR(dateStr: string): string {
  return new Intl.DateTimeFormat("tr-TR", {
    day: "numeric",
    month: "long",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(dateStr));
}

/** Alan aralığı formatı */
function formatAreaRange(min?: number, max?: number): string {
  if (!min && !max) return "Belirtilmemiş";
  if (min && max) return `${min} - ${max} m²`;
  if (min) return `Min ${min} m²`;
  if (max) return `Max ${max} m²`;
  return "Belirtilmemiş";
}

// --- Bileşen ---

interface CustomerInfoProps {
  customer: Customer;
}

export function CustomerInfo({ customer }: CustomerInfoProps) {
  const typeConfig = CUSTOMER_TYPE_CONFIG[customer.customer_type];
  const statusConfig = LEAD_STATUS_CONFIG[customer.lead_status];

  return (
    <div className="space-y-8">
      {/* Müşteri Tercihleri */}
      <div>
        <h3 className="text-lg font-medium leading-6 text-gray-900 border-b border-gray-200 pb-2 mb-4">
          Müşteri Tercihleri
        </h3>
        <div className="grid grid-cols-1 gap-y-6 gap-x-4 sm:grid-cols-2">
          {/* Müşteri Tipi */}
          <div>
            <dt className="text-sm font-medium text-gray-500">Müşteri Tipi</dt>
            <dd className="mt-1">
              <span
                className={cn(
                  "inline-flex items-center px-2.5 py-1 rounded text-sm font-medium",
                  typeConfig.className
                )}
              >
                {typeConfig.label}
              </span>
            </dd>
          </div>

          {/* Lead Durumu */}
          <div>
            <dt className="text-sm font-medium text-gray-500">Lead Durumu</dt>
            <dd className="mt-1">
              <span
                className={cn(
                  "inline-flex items-center px-2.5 py-1 rounded text-sm font-medium",
                  statusConfig.className
                )}
              >
                {statusConfig.label}
              </span>
            </dd>
          </div>

          {/* Bütçe Aralığı */}
          <div>
            <dt className="text-sm font-medium text-gray-500">Bütçe Aralığı</dt>
            <dd className="mt-1 text-sm text-gray-900 bg-gray-50 p-2 rounded">
              {formatBudgetRange(customer.budget_min, customer.budget_max)}
            </dd>
          </div>

          {/* İstenen Oda */}
          <div>
            <dt className="text-sm font-medium text-gray-500">Tercih Edilen Oda</dt>
            <dd className="mt-1 text-sm text-gray-900 bg-gray-50 p-2 rounded">
              {customer.desired_rooms || "Belirtilmemiş"}
            </dd>
          </div>

          {/* Alan Tercihi */}
          <div>
            <dt className="text-sm font-medium text-gray-500">M² Aralığı</dt>
            <dd className="mt-1 text-sm text-gray-900 bg-gray-50 p-2 rounded">
              {formatAreaRange(customer.desired_area_min, customer.desired_area_max)}
            </dd>
          </div>

          {/* Kaynak */}
          <div>
            <dt className="text-sm font-medium text-gray-500">Kaynak</dt>
            <dd className="mt-1 text-sm text-gray-900 bg-gray-50 p-2 rounded">
              {customer.source
                ? SOURCE_LABELS[customer.source] || customer.source
                : "Belirtilmemiş"}
            </dd>
          </div>

          {/* Kayıt Tarihi */}
          <div>
            <dt className="text-sm font-medium text-gray-500">Kayıt Tarihi</dt>
            <dd className="mt-1 text-sm text-gray-900 bg-gray-50 p-2 rounded">
              {formatDateTR(customer.created_at)}
            </dd>
          </div>

          {/* Son İletişim */}
          <div>
            <dt className="text-sm font-medium text-gray-500">Son İletişim</dt>
            <dd className="mt-1 text-sm text-gray-900 bg-gray-50 p-2 rounded">
              {customer.last_contact_at
                ? formatDateTR(customer.last_contact_at)
                : formatDateTR(customer.updated_at)}
            </dd>
          </div>
        </div>
      </div>

      {/* Lokasyon Tercihleri */}
      <div>
        <h3 className="text-lg font-medium leading-6 text-gray-900 border-b border-gray-200 pb-2 mb-4">
          Lokasyon Tercihleri
        </h3>
        {customer.desired_districts.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {customer.desired_districts.map((district) => (
              <span
                key={district}
                className="inline-flex items-center px-3 py-1.5 rounded-md text-sm font-medium bg-indigo-50 text-indigo-700 border border-indigo-100 capitalize"
              >
                {district}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-gray-500">Bölge tercihi belirtilmemiş.</p>
        )}
      </div>

      {/* Etiketler */}
      {customer.tags.length > 0 && (
        <div>
          <h3 className="text-lg font-medium leading-6 text-gray-900 border-b border-gray-200 pb-2 mb-4">
            Etiketler
          </h3>
          <div className="flex flex-wrap gap-2">
            {customer.tags.map((tag) => (
              <span
                key={tag}
                className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-white border border-gray-300 text-gray-700"
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Notlar (genel not alanı) */}
      {customer.notes && (
        <div>
          <h3 className="text-lg font-medium leading-6 text-gray-900 border-b border-gray-200 pb-2 mb-4">
            Genel Not
          </h3>
          <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-md border border-gray-100">
            {customer.notes}
          </p>
        </div>
      )}
    </div>
  );
}
