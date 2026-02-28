"use client";

import { useRouter } from "next/navigation";
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

interface CustomerCardListProps {
  customers: Customer[];
}

export function CustomerCardList({ customers }: CustomerCardListProps) {
  const router = useRouter();

  if (customers.length === 0) {
    return (
      <div className="block sm:hidden px-4 py-12 text-center text-gray-500">
        <p className="text-sm">Müşteri bulunamadı.</p>
      </div>
    );
  }

  return (
    <div className="block sm:hidden space-y-3">
      {customers.map((customer) => {
        const statusConfig = LEAD_STATUS_CONFIG[customer.lead_status];
        const typeConfig = CUSTOMER_TYPE_CONFIG[customer.customer_type];
        const initials = getInitials(customer.full_name);

        return (
          <div
            key={customer.id}
            onClick={() =>
              router.push(`/dashboard/customers/${customer.id}`)
            }
            className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer"
          >
            {/* Header: Avatar + Name + Status */}
            <div className="flex justify-between items-start mb-3">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-indigo-100 flex items-center justify-center text-blue-600 font-bold text-sm">
                  {initials}
                </div>
                <div>
                  <h3 className="text-sm font-medium text-blue-600">
                    {customer.full_name}
                  </h3>
                  <p className="text-xs text-gray-500">
                    {customer.phone || customer.email || "-"}
                  </p>
                </div>
              </div>
              <span
                className={cn(
                  "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
                  statusConfig.className
                )}
              >
                {statusConfig.label}
              </span>
            </div>

            {/* Footer: Type + Budget */}
            <div className="flex items-center justify-between">
              <span
                className={cn(
                  "inline-flex items-center px-2 py-0.5 rounded text-xs font-medium",
                  typeConfig.className
                )}
              >
                {typeConfig.label}
              </span>
              <span className="text-sm text-gray-700 font-medium">
                {formatBudget(customer.budget_min, customer.budget_max)}
              </span>
            </div>
          </div>
        );
      })}
    </div>
  );
}
