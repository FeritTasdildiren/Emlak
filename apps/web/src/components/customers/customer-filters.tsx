"use client";

import { Search, X } from "lucide-react";
import type { CustomerType, LeadStatus } from "@/types/customer";

interface CustomerFiltersProps {
  search: string;
  onSearchChange: (value: string) => void;
  leadStatus: LeadStatus | null;
  onLeadStatusChange: (value: LeadStatus | null) => void;
  customerType: CustomerType | null;
  onCustomerTypeChange: (value: CustomerType | null) => void;
}

const LEAD_STATUS_OPTIONS: { value: LeadStatus; label: string }[] = [
  { value: "cold", label: "Soğuk" },
  { value: "warm", label: "Ilık" },
  { value: "hot", label: "Sıcak" },
  { value: "converted", label: "Dönüşüm" },
  { value: "lost", label: "Kayıp" },
];

const CUSTOMER_TYPE_OPTIONS: { value: CustomerType; label: string }[] = [
  { value: "buyer", label: "Alıcı" },
  { value: "seller", label: "Satıcı" },
  { value: "renter", label: "Kiracı" },
  { value: "landlord", label: "Ev Sahibi" },
];

export function CustomerFilters({
  search,
  onSearchChange,
  leadStatus,
  onLeadStatusChange,
  customerType,
  onCustomerTypeChange,
}: CustomerFiltersProps) {
  const hasActiveFilters = search || leadStatus || customerType;

  const handleClearFilters = () => {
    onSearchChange("");
    onLeadStatusChange(null);
    onCustomerTypeChange(null);
  };

  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Search */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-gray-400" />
          </div>
          <input
            type="text"
            value={search}
            onChange={(e) => onSearchChange(e.target.value)}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:ring-1 focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
            placeholder="İsim, telefon veya email ara..."
          />
        </div>

        {/* Lead Status Select */}
        <select
          value={leadStatus || ""}
          onChange={(e) =>
            onLeadStatusChange(
              e.target.value ? (e.target.value as LeadStatus) : null
            )
          }
          className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
        >
          <option value="">Durum: Tümü</option>
          {LEAD_STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        {/* Customer Type Select */}
        <select
          value={customerType || ""}
          onChange={(e) =>
            onCustomerTypeChange(
              e.target.value ? (e.target.value as CustomerType) : null
            )
          }
          className="block w-full pl-3 pr-10 py-2 text-base border border-gray-300 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm rounded-md"
        >
          <option value="">Müşteri Tipi: Tümü</option>
          {CUSTOMER_TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>
      </div>

      {hasActiveFilters && (
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-xs font-medium text-gray-500 uppercase">
              Aktif Filtreler:
            </span>
            {customerType && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
                Tip:{" "}
                {
                  CUSTOMER_TYPE_OPTIONS.find((o) => o.value === customerType)
                    ?.label
                }
                <button
                  type="button"
                  onClick={() => onCustomerTypeChange(null)}
                  className="ml-1.5 inline-flex text-indigo-500 hover:text-indigo-600"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {leadStatus && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
                Durum:{" "}
                {
                  LEAD_STATUS_OPTIONS.find((o) => o.value === leadStatus)?.label
                }
                <button
                  type="button"
                  onClick={() => onLeadStatusChange(null)}
                  className="ml-1.5 inline-flex text-indigo-500 hover:text-indigo-600"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {search && (
              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-100 text-indigo-800">
                Arama: &quot;{search}&quot;
                <button
                  type="button"
                  onClick={() => onSearchChange("")}
                  className="ml-1.5 inline-flex text-indigo-500 hover:text-indigo-600"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
          </div>
          <button
            onClick={handleClearFilters}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            Filtreleri Temizle
          </button>
        </div>
      )}
    </div>
  );
}
