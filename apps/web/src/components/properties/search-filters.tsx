"use client";

import { useState } from "react";
import {
  SlidersHorizontal,
  X,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import type { SearchFilters as SearchFiltersType } from "@/types/property";
import { cn } from "@/lib/utils";
import { getDefaultSearchFilters } from "@/hooks/use-search";

// Istanbul districts
const ISTANBUL_DISTRICTS = [
  "Adalar", "Arnavutköy", "Ataşehir", "Avcılar", "Bağcılar",
  "Bahçelievler", "Bakırköy", "Başakşehir", "Bayrampaşa", "Beşiktaş",
  "Beykoz", "Beylikdüzü", "Beyoğlu", "Büyükçekmece", "Çatalca",
  "Çekmeköy", "Esenler", "Esenyurt", "Eyüpsultan", "Fatih",
  "Gaziosmanpaşa", "Güngören", "Kadıköy", "Kağıthane", "Kartal",
  "Küçükçekmece", "Maltepe", "Pendik", "Sancaktepe", "Sarıyer",
  "Silivri", "Sultanbeyli", "Sultangazi", "Şile", "Şişli",
  "Tuzla", "Ümraniye", "Üsküdar", "Zeytinburnu",
];

const CITIES = ["İstanbul", "Ankara", "İzmir", "Bursa", "Antalya"];

const SORT_OPTIONS = [
  { value: "newest", label: "En Yeni" },
  { value: "price_asc", label: "Fiyat (Düşükten Yükseğe)" },
  { value: "price_desc", label: "Fiyat (Yüksekten Düşüğe)" },
  { value: "area_desc", label: "Alan (m²)" },
];

interface SearchFiltersProps {
  filters: SearchFiltersType;
  onChange: <K extends keyof SearchFiltersType>(
    key: K,
    value: SearchFiltersType[K]
  ) => void;
  onReset: () => void;
}

export function SearchFilters({
  filters,
  onChange,
  onReset,
}: SearchFiltersProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const defaults = getDefaultSearchFilters();
  const activeFilterCount = countActiveFilters(filters, defaults);

  return (
    <div className="rounded-lg border bg-white">
      {/* Toggle bar */}
      <button
        type="button"
        onClick={() => setIsExpanded((prev) => !prev)}
        className="flex w-full items-center justify-between px-4 py-3 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <SlidersHorizontal className="h-4 w-4" />
          <span>Filtreler</span>
          {activeFilterCount > 0 && (
            <Badge variant="default" className="ml-1">
              {activeFilterCount}
            </Badge>
          )}
        </div>
        {isExpanded ? (
          <ChevronUp className="h-4 w-4" />
        ) : (
          <ChevronDown className="h-4 w-4" />
        )}
      </button>

      {/* Filter panel */}
      {isExpanded && (
        <div className="border-t px-4 py-4 space-y-4">
          {/* Row 1: City + District + Sort */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
            {/* City */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                Şehir
              </label>
              <select
                value={filters.city}
                onChange={(e) => {
                  onChange("city", e.target.value);
                  if (e.target.value !== "İstanbul") {
                    onChange("district", "");
                  }
                }}
                className="h-9 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm outline-none transition-colors focus:border-blue-300 focus:ring-2 focus:ring-blue-100"
              >
                <option value="">Tüm Şehirler</option>
                {CITIES.map((city) => (
                  <option key={city} value={city}>
                    {city}
                  </option>
                ))}
              </select>
            </div>

            {/* District */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                İlçe
              </label>
              <select
                value={filters.district}
                onChange={(e) => onChange("district", e.target.value)}
                disabled={filters.city !== "İstanbul" && filters.city !== ""}
                className="h-9 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm outline-none transition-colors focus:border-blue-300 focus:ring-2 focus:ring-blue-100 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <option value="">Tüm İlçeler</option>
                {ISTANBUL_DISTRICTS.map((d) => (
                  <option key={d} value={d}>
                    {d}
                  </option>
                ))}
              </select>
            </div>

            {/* Sort */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                Sıralama
              </label>
              <select
                value={filters.sort}
                onChange={(e) => onChange("sort", e.target.value)}
                className="h-9 w-full rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm outline-none transition-colors focus:border-blue-300 focus:ring-2 focus:ring-blue-100"
              >
                {SORT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Row 2: Property Type + Listing Type */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {/* Property Type */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                Mülk Türü
              </label>
              <SegmentedControl
                value={filters.property_type}
                onChange={(v) =>
                  onChange("property_type", v as SearchFiltersType["property_type"])
                }
                options={[
                  { value: "all", label: "Tümü" },
                  { value: "daire", label: "Daire" },
                  { value: "villa", label: "Villa" },
                  { value: "ofis", label: "Ofis" },
                  { value: "arsa", label: "Arsa" },
                  { value: "dukkan", label: "Dükkan" },
                ]}
              />
            </div>

            {/* Listing Type */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                İlan Türü
              </label>
              <SegmentedControl
                value={filters.listing_type}
                onChange={(v) =>
                  onChange("listing_type", v as SearchFiltersType["listing_type"])
                }
                options={[
                  { value: "all", label: "Tümü" },
                  { value: "satilik", label: "Satılık" },
                  { value: "kiralik", label: "Kiralık" },
                ]}
              />
            </div>
          </div>

          {/* Row 3: Price Range + Area Range */}
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {/* Price Range */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                Fiyat Aralığı (₺)
              </label>
              <div className="flex items-center gap-2">
                <RangeInput
                  placeholder="Min"
                  value={filters.min_price}
                  onChange={(v) => onChange("min_price", v)}
                />
                <span className="text-gray-400">—</span>
                <RangeInput
                  placeholder="Max"
                  value={filters.max_price}
                  onChange={(v) => onChange("max_price", v)}
                />
              </div>
            </div>

            {/* Area Range */}
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                Alan Aralığı (m²)
              </label>
              <div className="flex items-center gap-2">
                <RangeInput
                  placeholder="Min"
                  value={filters.min_area}
                  onChange={(v) => onChange("min_area", v)}
                />
                <span className="text-gray-400">—</span>
                <RangeInput
                  placeholder="Max"
                  value={filters.max_area}
                  onChange={(v) => onChange("max_area", v)}
                />
              </div>
            </div>
          </div>

          {/* Row 4: Status + Clear */}
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-gray-500 uppercase tracking-wider">
                Durum
              </label>
              <SegmentedControl
                value={filters.status}
                onChange={(v) =>
                  onChange("status", v as SearchFiltersType["status"])
                }
                options={[
                  { value: "all", label: "Tümü" },
                  { value: "active", label: "Aktif" },
                  { value: "sold", label: "Satıldı" },
                  { value: "rented", label: "Kiralandı" },
                  { value: "draft", label: "Taslak" },
                ]}
              />
            </div>

            {activeFilterCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={onReset}
                className="text-gray-500 hover:text-red-600 shrink-0"
              >
                <X className="mr-1 h-3.5 w-3.5" />
                Filtreleri Temizle
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

// --- SegmentedControl ---

interface SegmentedControlProps {
  value: string;
  onChange: (value: string) => void;
  options: { value: string; label: string }[];
}

function SegmentedControl({ value, onChange, options }: SegmentedControlProps) {
  return (
    <div className="inline-flex rounded-lg border border-gray-200 bg-gray-50 p-0.5">
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className={cn(
            "rounded-md px-3 py-1.5 text-xs font-medium transition-all",
            value === opt.value
              ? "bg-white text-gray-900 shadow-sm"
              : "text-gray-500 hover:text-gray-700"
          )}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}

// --- RangeInput ---

interface RangeInputProps {
  placeholder: string;
  value: number | undefined;
  onChange: (value: number | undefined) => void;
}

function RangeInput({ placeholder, value, onChange }: RangeInputProps) {
  const formatForDisplay = (num: number) =>
    new Intl.NumberFormat("tr-TR").format(num);

  const [displayValue, setDisplayValue] = useState(
    value !== undefined ? formatForDisplay(value) : ""
  );

  function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
    const raw = e.target.value;
    // Allow only digits and dots (thousands separator)
    if (raw !== "" && !/^[\d.]+$/.test(raw)) return;
    setDisplayValue(raw);

    const cleaned = raw.replace(/\./g, "");
    const parsed = parseInt(cleaned, 10);
    onChange(isNaN(parsed) ? undefined : parsed);
  }

  function handleBlur() {
    if (value !== undefined) {
      setDisplayValue(formatForDisplay(value));
    } else {
      setDisplayValue("");
    }
  }

  return (
    <input
      type="text"
      inputMode="numeric"
      placeholder={placeholder}
      value={displayValue}
      onChange={handleChange}
      onBlur={handleBlur}
      className="h-9 w-full min-w-0 rounded-lg border border-gray-200 bg-gray-50 px-3 text-sm outline-none transition-colors placeholder:text-gray-400 focus:border-blue-300 focus:ring-2 focus:ring-blue-100"
    />
  );
}

// --- Helpers ---

function countActiveFilters(
  filters: SearchFiltersType,
  defaults: SearchFiltersType
): number {
  let count = 0;
  if (filters.city !== defaults.city) count++;
  if (filters.district !== defaults.district) count++;
  if (filters.property_type !== defaults.property_type) count++;
  if (filters.listing_type !== defaults.listing_type) count++;
  if (filters.status !== defaults.status) count++;
  if (filters.min_price !== defaults.min_price) count++;
  if (filters.max_price !== defaults.max_price) count++;
  if (filters.min_area !== defaults.min_area) count++;
  if (filters.max_area !== defaults.max_area) count++;
  if (filters.sort !== defaults.sort) count++;
  return count;
}
