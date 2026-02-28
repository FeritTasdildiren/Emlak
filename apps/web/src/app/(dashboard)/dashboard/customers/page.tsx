"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Plus, ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CustomerPipeline } from "@/components/customers/customer-pipeline";
import { CustomerFilters } from "@/components/customers/customer-filters";
import { CustomerTable } from "@/components/customers/customer-table";
import { CustomerCardList } from "@/components/customers/customer-card";
import { useCustomers } from "@/hooks/use-customers";
import type { CustomerType, LeadStatus } from "@/types/customer";
import { cn } from "@/lib/utils";

const PER_PAGE = 10;

export default function CustomersPage() {
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [leadStatus, setLeadStatus] = useState<LeadStatus | null>(null);
  const [customerType, setCustomerType] = useState<CustomerType | null>(null);
  const [page, setPage] = useState(1);

  const { customers, total, pipelineCounts } = useCustomers({
    search,
    leadStatus,
    customerType,
    page,
    perPage: PER_PAGE,
  });

  const totalPages = Math.ceil(total / PER_PAGE);
  const startItem = total > 0 ? (page - 1) * PER_PAGE + 1 : 0;
  const endItem = Math.min(page * PER_PAGE, total);

  const handleLeadStatusChange = (status: LeadStatus | null) => {
    setLeadStatus(status);
    setPage(1);
  };

  const handleCustomerTypeChange = (type: CustomerType | null) => {
    setCustomerType(type);
    setPage(1);
  };

  const handleSearchChange = (value: string) => {
    setSearch(value);
    setPage(1);
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 w-full max-w-7xl mx-auto space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold text-gray-900">Müşteriler</h1>
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
            {total}
          </span>
        </div>
        <Button onClick={() => router.push("/dashboard/customers/new")}>
          <Plus className="w-4 h-4 mr-2" />
          Yeni Müşteri
        </Button>
      </div>

      {/* Pipeline */}
      <CustomerPipeline
        counts={pipelineCounts}
        activeStatus={leadStatus}
        onStatusClick={handleLeadStatusChange}
      />

      {/* Filters */}
      <CustomerFilters
        search={search}
        onSearchChange={handleSearchChange}
        leadStatus={leadStatus}
        onLeadStatusChange={handleLeadStatusChange}
        customerType={customerType}
        onCustomerTypeChange={handleCustomerTypeChange}
      />

      {/* Customer List: Desktop Table + Mobile Cards */}
      <CustomerTable customers={customers} />
      <CustomerCardList customers={customers} />

      {/* Pagination */}
      {total > 0 && (
        <div className="bg-white px-4 py-3 flex items-center justify-between border border-gray-200 rounded-lg shadow-sm sm:px-6">
          {/* Mobile Pagination */}
          <div className="flex-1 flex justify-between sm:hidden">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Önceki
            </button>
            <span className="inline-flex items-center text-sm text-gray-700">
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Sonraki
            </button>
          </div>

          {/* Desktop Pagination */}
          <div className="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p className="text-sm text-gray-700">
                Toplam <span className="font-medium">{total}</span> kayıttan{" "}
                <span className="font-medium">{startItem}</span> ile{" "}
                <span className="font-medium">{endItem}</span> arası
                gösteriliyor
              </p>
            </div>
            <div>
              <nav className="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="sr-only">Önceki</span>
                  <ChevronLeft className="h-4 w-4" />
                </button>
                {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                  (p) => (
                    <button
                      key={p}
                      onClick={() => setPage(p)}
                      className={cn(
                        "relative inline-flex items-center px-4 py-2 border text-sm font-medium",
                        p === page
                          ? "z-10 bg-blue-50 border-blue-500 text-blue-600"
                          : "bg-white border-gray-300 text-gray-500 hover:bg-gray-50"
                      )}
                    >
                      {p}
                    </button>
                  )
                )}
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="sr-only">Sonraki</span>
                  <ChevronRight className="h-4 w-4" />
                </button>
              </nav>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
