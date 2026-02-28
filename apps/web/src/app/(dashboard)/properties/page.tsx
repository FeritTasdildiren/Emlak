"use client";

import { useCallback, useMemo, Suspense } from "react";
import Link from "next/link";
import { useSearchParams, useRouter, usePathname } from "next/navigation";
import { usePropertySearch, getDefaultSearchFilters } from "@/hooks/use-search";
import type {
  Property,
  PropertyType,
  PropertyStatus,
  SearchFilters,
} from "@/types/property";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { PropertyCard } from "@/components/properties/property-card";
import { SearchBar } from "@/components/properties/search-bar";
import { SearchFilters as SearchFiltersPanel } from "@/components/properties/search-filters";
import { cn, formatCurrency, formatDate } from "@/lib/utils";
import {
  Plus,
  Home,
  Building2,
  LandPlot,
  ChevronLeft,
  ChevronRight,
  LayoutGrid,
  LayoutList,
  PackageOpen,
  Search,
} from "lucide-react";
import { toast } from "@/components/ui/toast";

const statusConfig: Record<
  PropertyStatus,
  { label: string; variant: "success" | "default" | "warning" | "secondary" }
> = {
  active: { label: "Aktif", variant: "success" },
  sold: { label: "Satıldı", variant: "default" },
  rented: { label: "Kiralandı", variant: "warning" },
  draft: { label: "Taslak", variant: "secondary" },
};

const typeLabels: Record<PropertyType, string> = {
  daire: "Daire",
  villa: "Villa",
  ofis: "Ofis",
  arsa: "Arsa",
  dukkan: "Dükkan",
};

const typeIcons: Record<PropertyType, typeof Home> = {
  daire: Home,
  villa: Home,
  ofis: Building2,
  arsa: LandPlot,
  dukkan: Building2,
};

type ViewMode = "table" | "grid";

function parseSearchParams(params: URLSearchParams): SearchFilters {
  const defaults = getDefaultSearchFilters();
  return {
    q: params.get("q") || defaults.q,
    city: params.get("city") || defaults.city,
    district: params.get("district") || defaults.district,
    property_type:
      (params.get("property_type") as SearchFilters["property_type"]) ||
      defaults.property_type,
    listing_type:
      (params.get("listing_type") as SearchFilters["listing_type"]) ||
      defaults.listing_type,
    status:
      (params.get("status") as SearchFilters["status"]) || defaults.status,
    min_price: params.get("min_price")
      ? Number(params.get("min_price"))
      : defaults.min_price,
    max_price: params.get("max_price")
      ? Number(params.get("max_price"))
      : defaults.max_price,
    min_area: params.get("min_area")
      ? Number(params.get("min_area"))
      : defaults.min_area,
    max_area: params.get("max_area")
      ? Number(params.get("max_area"))
      : defaults.max_area,
    sort: params.get("sort") || defaults.sort,
    page: params.get("page") ? Number(params.get("page")) : defaults.page,
    per_page: params.get("per_page")
      ? Number(params.get("per_page"))
      : defaults.per_page,
  };
}

function filtersToParams(filters: SearchFilters): URLSearchParams {
  const defaults = getDefaultSearchFilters();
  const params = new URLSearchParams();

  if (filters.q !== defaults.q) params.set("q", filters.q);
  if (filters.city !== defaults.city) params.set("city", filters.city);
  if (filters.district !== defaults.district)
    params.set("district", filters.district);
  if (filters.property_type !== defaults.property_type)
    params.set("property_type", filters.property_type);
  if (filters.listing_type !== defaults.listing_type)
    params.set("listing_type", filters.listing_type);
  if (filters.status !== defaults.status)
    params.set("status", filters.status);
  if (filters.min_price !== undefined && filters.min_price !== defaults.min_price)
    params.set("min_price", String(filters.min_price));
  if (filters.max_price !== undefined && filters.max_price !== defaults.max_price)
    params.set("max_price", String(filters.max_price));
  if (filters.min_area !== undefined && filters.min_area !== defaults.min_area)
    params.set("min_area", String(filters.min_area));
  if (filters.max_area !== undefined && filters.max_area !== defaults.max_area)
    params.set("max_area", String(filters.max_area));
  if (filters.sort !== defaults.sort) params.set("sort", filters.sort);
  if (filters.page !== defaults.page)
    params.set("page", String(filters.page));

  return params;
}

// Wrap the page content in Suspense because useSearchParams requires it
export default function PropertiesPage() {
  return (
    <Suspense fallback={<LoadingSkeleton viewMode="table" />}>
      <PropertiesPageContent />
    </Suspense>
  );
}

function PropertiesPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const filters = useMemo(
    () => parseSearchParams(searchParams),
    [searchParams]
  );

  const viewModeParam = searchParams.get("view") as ViewMode | null;
  const viewMode: ViewMode = viewModeParam === "grid" ? "grid" : "table";

  const { data, isLoading } = usePropertySearch(filters);

  const updateURL = useCallback(
    (newFilters: SearchFilters, newView?: ViewMode) => {
      const params = filtersToParams(newFilters);
      const view = newView ?? viewMode;
      if (view === "grid") params.set("view", "grid");
      const qs = params.toString();
      router.replace(`${pathname}${qs ? `?${qs}` : ""}`, { scroll: false });
    },
    [router, pathname, viewMode]
  );

  const updateFilter = useCallback(
    <K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) => {
      const newFilters = {
        ...filters,
        [key]: value,
        page: key === "page" ? (value as number) : 1,
      };
      updateURL(newFilters);
    },
    [filters, updateURL]
  );

  const handleSearchSubmit = useCallback(
    (value: string) => {
      const newFilters = { ...filters, q: value, page: 1 };
      updateURL(newFilters);
    },
    [filters, updateURL]
  );

  const handleReset = useCallback(() => {
    const defaults = getDefaultSearchFilters();
    updateURL(defaults);
  }, [updateURL]);

  function setViewMode(mode: ViewMode) {
    updateURL(filters, mode);
  }

  function handlePropertyClick(property: Property) {
    toast(`${property.title} — Detay sayfası yakında eklenecek.`, "info");
  }

  const totalResults = data?.total ?? 0;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Portföy Yönetimi
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Portföyünüzdeki mülkleri buradan yönetebilirsiniz.
          </p>
        </div>
        <Link href="/properties/new">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            Yeni İlan Ekle
          </Button>
        </Link>
      </div>

      {/* Search Bar + View Toggle */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
        <SearchBar
          value={filters.q}
          onChange={() => {}}
          onSearch={handleSearchSubmit}
        />

        {/* View toggle */}
        <div className="hidden sm:flex items-center rounded-lg border border-gray-200 shrink-0">
          <button
            onClick={() => setViewMode("table")}
            className={cn(
              "flex h-10 w-10 items-center justify-center rounded-l-lg transition-colors",
              viewMode === "table"
                ? "bg-blue-50 text-blue-600"
                : "text-gray-400 hover:text-gray-600"
            )}
          >
            <LayoutList className="h-4 w-4" />
          </button>
          <button
            onClick={() => setViewMode("grid")}
            className={cn(
              "flex h-10 w-10 items-center justify-center rounded-r-lg transition-colors",
              viewMode === "grid"
                ? "bg-blue-50 text-blue-600"
                : "text-gray-400 hover:text-gray-600"
            )}
          >
            <LayoutGrid className="h-4 w-4" />
          </button>
        </div>
      </div>

      {/* Filters */}
      <SearchFiltersPanel
        filters={filters}
        onChange={updateFilter}
        onReset={handleReset}
      />

      {/* Result count */}
      {!isLoading && data && (
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <Search className="h-3.5 w-3.5" />
          <span>
            <span className="font-medium text-gray-900">{totalResults}</span>{" "}
            sonuç bulundu
          </span>
          {filters.q && (
            <span>
              — &ldquo;<span className="font-medium">{filters.q}</span>&rdquo;
            </span>
          )}
        </div>
      )}

      {/* Content */}
      {isLoading ? (
        <LoadingSkeleton viewMode={viewMode} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState hasFilters={filters.q !== ""} onReset={handleReset} />
      ) : viewMode === "table" ? (
        <PropertyTable
          properties={data.items}
          onPropertyClick={handlePropertyClick}
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data.items.map((property) => (
            <PropertyCard
              key={property.id}
              property={property}
              onClick={handlePropertyClick}
            />
          ))}
        </div>
      )}

      {/* Pagination */}
      {data && data.total_pages > 1 && (
        <div className="flex items-center justify-between rounded-lg border bg-white px-4 py-3">
          <p className="text-sm text-gray-500">
            Toplam{" "}
            <span className="font-medium text-gray-900">{data.total}</span>{" "}
            ilan
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={data.page <= 1}
              onClick={() => updateFilter("page", data.page - 1)}
            >
              <ChevronLeft className="mr-1 h-4 w-4" />
              Önceki
            </Button>
            <span className="text-sm text-gray-600">
              {data.page} / {data.total_pages}
            </span>
            <Button
              variant="outline"
              size="sm"
              disabled={data.page >= data.total_pages}
              onClick={() => updateFilter("page", data.page + 1)}
            >
              Sonraki
              <ChevronRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

function PropertyTable({
  properties,
  onPropertyClick,
}: {
  properties: Property[];
  onPropertyClick: (p: Property) => void;
}) {
  return (
    <div className="overflow-hidden rounded-lg border bg-white">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b bg-gray-50 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
              <th className="px-4 py-3">Başlık</th>
              <th className="px-4 py-3 hidden sm:table-cell">Tür</th>
              <th className="px-4 py-3">Fiyat</th>
              <th className="px-4 py-3 hidden md:table-cell">m²</th>
              <th className="px-4 py-3 hidden lg:table-cell">İlçe</th>
              <th className="px-4 py-3">Durum</th>
              <th className="px-4 py-3 hidden lg:table-cell">Tarih</th>
            </tr>
          </thead>
          <tbody className="divide-y">
            {properties.map((property) => {
              const status = statusConfig[property.status];
              const TypeIcon = typeIcons[property.property_type];
              return (
                <tr
                  key={property.id}
                  onClick={() => onPropertyClick(property)}
                  className="cursor-pointer transition-colors hover:bg-gray-50"
                >
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600 sm:hidden">
                        <TypeIcon className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="truncate font-medium text-gray-900 max-w-[200px] lg:max-w-[300px]">
                          {property.title}
                        </p>
                        <p className="text-xs text-gray-400 sm:hidden">
                          {typeLabels[property.property_type]} ·{" "}
                          {property.district}
                        </p>
                      </div>
                    </div>
                  </td>
                  <td className="px-4 py-3 hidden sm:table-cell">
                    <div className="flex items-center gap-2">
                      <TypeIcon className="h-4 w-4 text-gray-400" />
                      <span className="text-gray-600">
                        {typeLabels[property.property_type]}
                      </span>
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <div>
                      <p className="font-medium text-gray-900">
                        {formatCurrency(property.price)}
                      </p>
                      {property.listing_type === "kiralik" && (
                        <p className="text-xs text-gray-400">/ay</p>
                      )}
                    </div>
                  </td>
                  <td className="px-4 py-3 hidden md:table-cell text-gray-600">
                    {property.area_sqm} m²
                  </td>
                  <td className="px-4 py-3 hidden lg:table-cell text-gray-600">
                    {property.district}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={status.variant}>{status.label}</Badge>
                  </td>
                  <td className="px-4 py-3 hidden lg:table-cell text-gray-500">
                    {formatDate(property.created_at)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function LoadingSkeleton({ viewMode }: { viewMode: ViewMode }) {
  if (viewMode === "grid") {
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div
            key={i}
            className="animate-pulse rounded-lg border bg-white p-4"
          >
            <div className="flex items-start gap-3">
              <div className="h-10 w-10 rounded-lg bg-gray-200" />
              <div className="flex-1 space-y-2">
                <div className="h-4 w-3/4 rounded bg-gray-200" />
                <div className="h-3 w-1/2 rounded bg-gray-200" />
              </div>
            </div>
            <div className="mt-4 flex justify-between">
              <div className="h-3 w-1/3 rounded bg-gray-200" />
              <div className="h-4 w-1/4 rounded bg-gray-200" />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-lg border bg-white">
      <div className="border-b bg-gray-50 px-4 py-3">
        <div className="flex gap-8">
          {Array.from({ length: 7 }).map((_, i) => (
            <div key={i} className="h-3 w-16 rounded bg-gray-200" />
          ))}
        </div>
      </div>
      {Array.from({ length: 5 }).map((_, i) => (
        <div
          key={i}
          className="flex items-center gap-4 border-b px-4 py-3"
        >
          <div className="h-8 w-8 rounded-lg bg-gray-100" />
          <div className="flex-1 space-y-1.5">
            <div className="h-4 w-1/3 rounded bg-gray-100" />
            <div className="h-3 w-1/5 rounded bg-gray-100 sm:hidden" />
          </div>
          <div className="hidden sm:block h-4 w-14 rounded bg-gray-100" />
          <div className="h-4 w-24 rounded bg-gray-100" />
          <div className="hidden md:block h-4 w-12 rounded bg-gray-100" />
          <div className="hidden lg:block h-4 w-16 rounded bg-gray-100" />
          <div className="h-5 w-16 rounded-full bg-gray-100" />
          <div className="hidden lg:block h-4 w-24 rounded bg-gray-100" />
        </div>
      ))}
    </div>
  );
}

function EmptyState({
  hasFilters,
  onReset,
}: {
  hasFilters: boolean;
  onReset: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-gray-200 bg-white py-16">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
        <PackageOpen className="h-8 w-8 text-gray-400" />
      </div>
      <h3 className="mt-4 text-lg font-medium text-gray-900">
        {hasFilters
          ? "Aramanızla eşleşen ilan bulunamadı"
          : "Henüz ilan eklenmemiş"}
      </h3>
      <p className="mt-1 text-sm text-gray-500">
        {hasFilters
          ? "Filtrelerinizi değiştirerek tekrar deneyebilirsiniz."
          : "Portföyünüze ilk ilanınızı ekleyerek başlayın."}
      </p>
      {hasFilters ? (
        <Button variant="outline" className="mt-6" onClick={onReset}>
          Filtreleri Temizle
        </Button>
      ) : (
        <Link href="/properties/new">
          <Button className="mt-6">
            <Plus className="mr-2 h-4 w-4" />
            Yeni İlan Ekle
          </Button>
        </Link>
      )}
    </div>
  );
}
