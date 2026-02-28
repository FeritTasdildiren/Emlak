"use client";

import { useRouter } from "next/navigation";
import { MoreVertical } from "lucide-react";
import type { Customer, CustomerType, LeadStatus } from "@/types/customer";
import { cn } from "@/lib/utils";

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

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

function formatBudget(min?: number, max?: number): string {
  if (!min && !max) return "-";
  const format = (n: number) => {
    if (n >= 1_000_000) {
      const val = n / 1_000_000;
      return `${val % 1 === 0 ? val.toFixed(0) : val.toFixed(1)}M`;
    }
    if (n >= 1_000) {
      const val = n / 1_000;
      return `${val % 1 === 0 ? val.toFixed(0) : val.toFixed(1)}K`;
    }
    return n.toLocaleString("tr-TR");
  };

  if (min && max) return `${format(min)} - ${format(max)} TL`;
  if (min) return `${format(min)}+ TL`;
  if (max) return `${format(max)} TL`;
  return "-";
}

function getRelativeTime(dateStr: string): string {
  const now = new Date();
  const date = new Date(dateStr);
  const diffMs = now.getTime() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  const diffHour = Math.floor(diffMin / 60);
  const diffDay = Math.floor(diffHour / 24);
  const diffWeek = Math.floor(diffDay / 7);
  const diffMonth = Math.floor(diffDay / 30);
  const diffYear = Math.floor(diffDay / 365);

  if (diffMin < 1) return "az önce";
  if (diffMin < 60) return `${diffMin} dakika önce`;
  if (diffHour < 24) return `${diffHour} saat önce`;
  if (diffDay < 7) return `${diffDay} gün önce`;
  if (diffWeek < 4) return `${diffWeek} hafta önce`;
  if (diffMonth < 12) return `${diffMonth} ay önce`;
  return `${diffYear} yıl önce`;
}

interface CustomerTableProps {
  customers: Customer[];
}

export function CustomerTable({ customers }: CustomerTableProps) {
  const router = useRouter();

  return (
    <div className="hidden sm:block bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden">
      {/* Table Header */}
      <div className="grid grid-cols-12 gap-4 px-6 py-3 bg-gray-50 border-b border-gray-200 text-xs font-medium text-gray-500 uppercase tracking-wider">
        <div className="col-span-3">Müşteri</div>
        <div className="col-span-2">Tip / Durum</div>
        <div className="col-span-2">Bütçe</div>
        <div className="col-span-3">İlgi Alanı</div>
        <div className="col-span-2 text-right">Son İletişim</div>
      </div>

      {/* Table Body */}
      <ul className="divide-y divide-gray-200">
        {customers.map((customer) => {
          const statusConfig = LEAD_STATUS_CONFIG[customer.lead_status];
          const typeConfig = CUSTOMER_TYPE_CONFIG[customer.customer_type];
          const initials = getInitials(customer.full_name);
          const lastContact = customer.last_contact_at || customer.updated_at;

          return (
            <li
              key={customer.id}
              onClick={() =>
                router.push(`/dashboard/customers/${customer.id}`)
              }
              className="group hover:bg-gray-50 transition-colors cursor-pointer"
            >
              <div className="px-6 py-4">
                <div className="grid grid-cols-12 gap-4 items-center">
                  {/* Name & Contact */}
                  <div className="col-span-3 flex items-center gap-3">
                    <div className="h-9 w-9 rounded-full bg-indigo-100 flex items-center justify-center text-blue-600 font-bold text-sm shrink-0">
                      {initials}
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-blue-600 truncate">
                        {customer.full_name}
                      </p>
                      <p className="text-xs text-gray-500 truncate">
                        {customer.phone || customer.email || "-"}
                      </p>
                    </div>
                  </div>

                  {/* Type & Status */}
                  <div className="col-span-2 flex items-center gap-2 flex-wrap">
                    <span
                      className={cn(
                        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
                        typeConfig.className
                      )}
                    >
                      {typeConfig.label}
                    </span>
                    <span
                      className={cn(
                        "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
                        statusConfig.className
                      )}
                    >
                      {statusConfig.label}
                    </span>
                  </div>

                  {/* Budget */}
                  <div className="col-span-2">
                    <div className="text-sm text-gray-900">
                      {formatBudget(customer.budget_min, customer.budget_max)}
                    </div>
                  </div>

                  {/* Locations */}
                  <div className="col-span-3">
                    <div className="flex flex-wrap gap-1">
                      {customer.desired_districts?.slice(0, 2).map((district) => (
                        <span
                          key={district}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800 capitalize"
                        >
                          {district}
                        </span>
                      ))}
                      {(customer.desired_districts?.length ?? 0) > 2 && (
                        <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600">
                          +{(customer.desired_districts?.length ?? 0) - 2}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Last Contact & Actions */}
                  <div className="col-span-2 text-right flex items-center justify-end gap-3">
                    <span className="text-xs text-gray-500">
                      {getRelativeTime(lastContact)}
                    </span>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                      }}
                      className="text-gray-400 hover:text-gray-600 p-1 rounded-full hover:bg-gray-100"
                    >
                      <MoreVertical className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>

      {customers.length === 0 && (
        <div className="px-6 py-12 text-center text-gray-500">
          <p className="text-sm">Müşteri bulunamadı.</p>
        </div>
      )}
    </div>
  );
}
