"use client";

import { useCallback, useMemo, useState } from "react";
import { SegmentedControl } from "@/app/tg/components/segmented-control";
import { TgSkeleton } from "@/app/tg/components/tg-skeleton";
import { useTgValuation } from "@/app/tg/hooks/use-tg-valuation";
import type { ValuationRequest, ValuationResponse } from "@/app/tg/lib/tg-api";
import {
  AlertTriangle,
  Calculator,
  ChevronDown,
  Download,
  Ruler,
  Share2,
  Sparkles,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ================================================================
// Types
// ================================================================

type ValuationPageState = "form" | "loading" | "result" | "error";

// ================================================================
// Static Data — İstanbul İlçeleri & Mahalleler
// ================================================================

const ISTANBUL_DISTRICTS = [
  "Adalar", "Arnavutköy", "Ataşehir", "Avcılar", "Bağcılar",
  "Bahçelievler", "Bakırköy", "Başakşehir", "Bayrampaşa", "Beşiktaş",
  "Beykoz", "Beylikdüzü", "Beyoğlu", "Büyükçekmece", "Çatalca",
  "Çekmeköy", "Esenler", "Esenyurt", "Eyüpsultan", "Fatih",
  "Gaziosmanpaşa", "Güngören", "Kadıköy", "Kağıthane", "Kartal",
  "Küçükçekmece", "Maltepe", "Pendik", "Sancaktepe", "Sarıyer",
  "Şile", "Silivri", "Şişli", "Sultanbeyli", "Sultangazi",
  "Tuzla", "Ümraniye", "Üsküdar",
];

const NEIGHBORHOOD_MAP: Record<string, string[]> = {
  Kadıköy: ["Caferağa", "Fenerbahçe", "Göztepe", "Kozyatağı", "Bostancı", "Suadiye", "Erenköy", "Fikirtepe", "Acıbadem", "Rasimpaşa"],
  Beşiktaş: ["Levent", "Etiler", "Bebek", "Ortaköy", "Arnavutköy", "Konaklar", "Ulus", "Nisbetiye", "Abbasağa", "Sinanpaşa"],
  Üsküdar: ["Acıbadem", "Altunizade", "Çengelköy", "Kısıklı", "Beylerbeyi", "Kandilli", "Ünalan", "Bulgurlu", "Küplüce", "Selimiye"],
  Şişli: ["Nişantaşı", "Teşvikiye", "Bomonti", "Harbiye", "Osmanbey", "Mecidiyeköy", "Esentepe", "Fulya", "Kuştepe", "Halaskargazi"],
  Bakırköy: ["Ataköy", "Florya", "Yeşilköy", "Bahçelievler", "Osmaniye", "Zuhuratbaba", "Cevizlik", "Kartaltepe", "Yenimahalle", "Sakızağacı"],
  Ataşehir: ["İçerenköy", "Kayışdağı", "Küçükbakkalköy", "Yenisahra", "Barbaros", "Ferhatpaşa", "Mustafa Kemal", "Esatpaşa", "Örnek"],
  Sarıyer: ["Maslak", "İstinye", "Tarabya", "Emirgan", "Rumelihisarı", "Baltalimanı", "Yeniköy", "Büyükdere"],
  Maltepe: ["Bağlarbaşı", "Cevizli", "Feyzullah", "Girne", "Gülsuyu", "İdealtepe", "Küçükyalı", "Zümrütevler"],
  Kartal: ["Soğanlık", "Yakacık", "Topselvi", "Kordonboyu", "Hürriyet", "Uğur Mumcu", "Atalar"],
  Pendik: ["Kaynarca", "Kurtköy", "Yenişehir", "Batı", "Doğu", "Güzelyalı", "Velibaba", "Esenler"],
};

const ROOM_OPTIONS = ["1+0", "1+1", "2+1", "3+1", "4+1", "5+"];
const AGE_OPTIONS = ["0-5", "6-10", "11-20", "21-30", "30+"];
const PROPERTY_TYPES = ["Apartman", "Rezidans", "Müstakil", "Villa"];

// ================================================================
// Helpers — form → API mapping
// ================================================================

/** "2+1" → { room_count: 2, living_room_count: 1 } */
function parseRooms(rooms: string): { room_count: number; living_room_count: number } {
  if (rooms === "5+") return { room_count: 5, living_room_count: 1 };
  const parts = rooms.split("+");
  return {
    room_count: Number(parts[0]) || 1,
    living_room_count: Number(parts[1]) || 0,
  };
}

/** "0-5" → 2 (ortanca) */
function parseAge(ageRange: string): number {
  if (ageRange === "30+") return 35;
  const parts = ageRange.split("-");
  const min = Number(parts[0]) || 0;
  const max = Number(parts[1]) || 0;
  return Math.round((min + max) / 2);
}

/** "Apartman" → "apartment" (API property_type) */
function mapPropertyType(label: string): string {
  const map: Record<string, string> = {
    Apartman: "apartment",
    Rezidans: "residence",
    Müstakil: "detached",
    Villa: "villa",
  };
  return map[label] ?? "apartment";
}

// ================================================================
// Valuation Page
// ================================================================

export default function TGValuationPage() {
  const [pageState, setPageState] = useState<ValuationPageState>("form");

  // Form state
  const [district, setDistrict] = useState("");
  const [neighborhood, setNeighborhood] = useState("");
  const [sqm, setSqm] = useState(120);
  const [rooms, setRooms] = useState("2+1");
  const [buildingAge, setBuildingAge] = useState("0-5");
  const [floor, setFloor] = useState("5");
  const [propertyType, setPropertyType] = useState("Apartman");

  // API mutation
  const valuation = useTgValuation();

  const neighborhoods = useMemo(
    () => NEIGHBORHOOD_MAP[district] ?? [],
    [district],
  );

  const handleDistrictChange = useCallback(
    (value: string) => {
      setDistrict(value);
      setNeighborhood("");
    },
    [],
  );

  const handleCalculate = useCallback(() => {
    setPageState("loading");

    const { room_count, living_room_count } = parseRooms(rooms);

    const body: ValuationRequest = {
      district,
      neighborhood: neighborhood || undefined,
      property_type: mapPropertyType(propertyType),
      net_sqm: sqm,
      gross_sqm: Math.round(sqm * 1.15), // ~%15 brüt fark tahmini
      room_count,
      living_room_count,
      floor: Number(floor) || 0,
      total_floors: Math.max(Number(floor) + 3, 5),
      building_age: parseAge(buildingAge),
      heating_type: "kombi",
    };

    valuation.mutate(body, {
      onSuccess: () => setPageState("result"),
      onError: () => setPageState("error"),
    });
  }, [district, neighborhood, sqm, rooms, buildingAge, floor, propertyType, valuation]);

  const handleNewValuation = useCallback(() => {
    valuation.reset();
    setPageState("form");
  }, [valuation]);

  // --- Loading State (Skeleton) ---
  if (pageState === "loading") {
    return <ValuationSkeleton />;
  }

  // --- Error State ---
  if (pageState === "error") {
    return (
      <ValuationError
        message={valuation.error}
        isQuotaExceeded={valuation.isQuotaExceeded}
        onRetry={handleNewValuation}
      />
    );
  }

  // --- Result State ---
  if (pageState === "result" && valuation.data) {
    return (
      <ValuationResultView
        result={valuation.data}
        sqm={sqm}
        onNewValuation={handleNewValuation}
      />
    );
  }

  // --- Form State ---
  return (
    <div className="space-y-4 pb-4">
      {/* Header */}
      <div>
        <h1 className="text-lg font-bold">Hızlı Değerleme</h1>
        <p className="text-sm text-slate-400">
          Yapay zeka destekli fiyat tahmini
        </p>
      </div>

      {/* İlçe */}
      <FormField label="İlçe">
        <SelectInput
          value={district}
          onChange={handleDistrictChange}
          placeholder="İlçe seçin..."
          options={ISTANBUL_DISTRICTS}
        />
      </FormField>

      {/* Mahalle */}
      <FormField label="Mahalle">
        <SelectInput
          value={neighborhood}
          onChange={setNeighborhood}
          placeholder={district ? "Mahalle seçin..." : "Önce ilçe seçin..."}
          options={neighborhoods}
          disabled={!district}
        />
      </FormField>

      {/* Alan m² */}
      <FormField label="Alan (m²)">
        <div className="flex items-center gap-3">
          <input
            type="number"
            min={30}
            max={500}
            value={sqm}
            onChange={(e) => setSqm(Number(e.target.value) || 30)}
            className="w-24 min-h-[44px] rounded-xl border border-slate-200 bg-white px-4 py-3 text-center font-mono text-sm focus:border-orange-500 focus:ring-2 focus:ring-orange-500 focus:outline-none"
          />
          <input
            type="range"
            min={30}
            max={500}
            value={sqm}
            onChange={(e) => setSqm(Number(e.target.value))}
            className="flex-1 accent-orange-600"
          />
        </div>
        <div className="mt-1 flex justify-between px-1 font-mono text-[11px] text-slate-400">
          <span>30m²</span>
          <span>500m²</span>
        </div>
      </FormField>

      {/* Oda Sayısı */}
      <FormField label="Oda Sayısı">
        <SegmentedControl
          options={ROOM_OPTIONS}
          value={rooms}
          onChange={setRooms}
        />
      </FormField>

      {/* Bina Yaşı */}
      <FormField label="Bina Yaşı">
        <SegmentedControl
          options={AGE_OPTIONS}
          value={buildingAge}
          onChange={setBuildingAge}
        />
      </FormField>

      {/* Kat */}
      <FormField label="Kat">
        <input
          type="number"
          min={0}
          max={30}
          value={floor}
          onChange={(e) => setFloor(e.target.value)}
          placeholder="0-30"
          className="w-full min-h-[44px] rounded-xl border border-slate-200 bg-white px-4 py-3 font-mono text-sm focus:border-orange-500 focus:ring-2 focus:ring-orange-500 focus:outline-none"
        />
      </FormField>

      {/* Yapı Tipi */}
      <FormField label="Yapı Tipi">
        <SelectInput
          value={propertyType}
          onChange={setPropertyType}
          options={PROPERTY_TYPES}
        />
      </FormField>

      {/* Calculate Button */}
      <button
        type="button"
        onClick={handleCalculate}
        disabled={!district || valuation.isPending}
        className={cn(
          "flex w-full min-h-[48px] items-center justify-center gap-2 rounded-xl py-3.5 text-sm font-semibold text-white shadow-lg shadow-orange-600/20 transition-all active:scale-[0.98]",
          district && !valuation.isPending
            ? "bg-orange-600 hover:bg-orange-700"
            : "cursor-not-allowed bg-slate-300",
        )}
      >
        <Sparkles className="h-4 w-4" />
        Değerleme Hesapla
      </button>

      {/* MAPE badge */}
      <div className="flex items-center justify-center gap-2 text-xs text-slate-400">
        <Zap className="h-3.5 w-3.5 text-orange-500" />
        <span>Ortalama MAPE: %9.94</span>
      </div>
    </div>
  );
}

// ================================================================
// Result View
// ================================================================

function ValuationResultView({
  result,
  sqm,
  onNewValuation,
}: {
  result: ValuationResponse;
  sqm: number;
  onNewValuation: () => void;
}) {
  const formatPrice = (n: number) =>
    new Intl.NumberFormat("tr-TR").format(n);
  const formatShort = (n: number) => {
    if (n >= 1_000_000) return `₺${(n / 1_000_000).toFixed(1)}M`;
    if (n >= 1_000) return `₺${(n / 1_000).toFixed(0)}K`;
    return `₺${n}`;
  };

  const price = result.estimated_price;
  const margin = Math.round((result.max_price - result.min_price) / 2);
  const confidence = Math.round(result.confidence * 100);
  const confidenceLabel = confidence >= 80 ? "Yüksek" : confidence >= 60 ? "Orta" : "Düşük";
  const pricePerSqm = result.price_per_sqm || Math.round(price / sqm);

  // marker: price'in min-max araligindaki pozisyonu
  const range = result.max_price - result.min_price;
  const markerPosition = range > 0
    ? Math.round(((price - result.min_price) / range) * 100)
    : 50;

  return (
    <div className="space-y-4 pb-4">
      <div>
        <h1 className="text-lg font-bold">Değerleme Sonucu</h1>
        <p className="text-sm text-slate-400">Yapay zeka destekli fiyat tahmini</p>
      </div>

      <div className="overflow-hidden rounded-2xl border border-slate-100 bg-white shadow-lg">
        {/* Result Header */}
        <div className="bg-gradient-to-r from-orange-500 to-orange-700 p-4 text-center text-white">
          <p className="mb-1 text-sm text-white/80">Tahmini Piyasa Değeri</p>
          <p className="font-mono text-3xl font-bold">
            ₺{formatPrice(price)}
          </p>
          <p className="mt-1 text-sm text-white/70">
            ± ₺{formatPrice(margin)}
          </p>
        </div>

        {/* Price Range Bar */}
        <div className="px-4 pb-2 pt-4">
          <div className="mb-2 flex justify-between text-xs text-slate-500">
            <span className="font-mono">{formatShort(result.min_price)}</span>
            <span className="font-semibold text-slate-700">Fiyat Aralığı</span>
            <span className="font-mono">{formatShort(result.max_price)}</span>
          </div>
          <div className="relative h-3 rounded-full bg-gradient-to-r from-emerald-400 via-orange-500 to-rose-400">
            <div
              className="absolute top-1/2 h-4 w-4 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-orange-600 bg-white shadow-md"
              style={{ left: `${markerPosition}%` }}
            />
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 gap-3 p-4">
          {/* Confidence */}
          <div className="flex items-center gap-3">
            <div
              className="flex h-14 w-14 items-center justify-center rounded-full"
              style={{
                background: `conic-gradient(#ea580c 0deg, #ea580c ${confidence * 3.6}deg, #e2e8f0 ${confidence * 3.6}deg)`,
              }}
            >
              <div className="flex h-11 w-11 items-center justify-center rounded-full bg-white">
                <span className="font-mono text-xs font-bold text-orange-600">
                  %{confidence}
                </span>
              </div>
            </div>
            <div>
              <p className="text-xs text-slate-400">Güven</p>
              <p className="text-sm font-semibold">{confidenceLabel}</p>
            </div>
          </div>

          {/* m² price */}
          <div className="flex items-center gap-3">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-purple-50">
              <Ruler className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-xs text-slate-400">m² Fiyat</p>
              <p className="font-mono text-sm font-bold">
                ₺{formatPrice(pricePerSqm)}
              </p>
            </div>
          </div>
        </div>

        {/* Quota Info */}
        {result.quota_remaining !== undefined && (
          <div className="mx-4 mb-3 rounded-lg bg-purple-50 px-3 py-2 text-center text-xs text-purple-700">
            Kalan kota: <strong>{result.quota_remaining}</strong> / {result.quota_limit}
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex gap-3 px-4 pb-4">
          <button
            type="button"
            className="flex min-h-[44px] flex-1 items-center justify-center gap-1.5 rounded-xl bg-orange-600 py-2.5 text-sm font-semibold text-white"
          >
            <Download className="h-4 w-4" />
            PDF İndir
          </button>
          <button
            type="button"
            className="flex min-h-[44px] flex-1 items-center justify-center gap-1.5 rounded-xl border border-slate-200 bg-white py-2.5 text-sm font-semibold text-slate-700"
          >
            <Share2 className="h-4 w-4" />
            Paylaş
          </button>
        </div>
      </div>

      {/* New Valuation */}
      <button
        type="button"
        onClick={onNewValuation}
        className="flex w-full items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white py-3 text-sm font-semibold text-slate-700 transition-all active:scale-[0.98]"
      >
        <Calculator className="h-4 w-4" />
        Yeni Değerleme
      </button>
    </div>
  );
}

// ================================================================
// Error State
// ================================================================

function ValuationError({
  message,
  isQuotaExceeded,
  onRetry,
}: {
  message: string | null;
  isQuotaExceeded: boolean;
  onRetry: () => void;
}) {
  return (
    <div className="flex flex-col items-center justify-center px-8 pt-20 text-center">
      <div
        className={cn(
          "mb-4 flex h-20 w-20 items-center justify-center rounded-full",
          isQuotaExceeded ? "bg-amber-50" : "bg-rose-50",
        )}
      >
        <AlertTriangle
          className={cn(
            "h-10 w-10",
            isQuotaExceeded ? "text-amber-400" : "text-rose-400",
          )}
        />
      </div>
      <h2 className="mb-2 text-lg font-semibold text-slate-700">
        {isQuotaExceeded ? "Kota Aşıldı" : "Değerleme Yapılamadı"}
      </h2>
      <p className="mb-6 text-sm text-slate-400">
        {message ?? "Bilinmeyen bir hata oluştu."}
      </p>
      <button
        type="button"
        onClick={onRetry}
        className="flex items-center gap-2 rounded-xl bg-orange-600 px-6 py-3 text-sm font-semibold text-white"
      >
        <Calculator className="h-4 w-4" />
        Tekrar Dene
      </button>
    </div>
  );
}

// ================================================================
// Loading Skeleton
// ================================================================

function ValuationSkeleton() {
  return (
    <div className="space-y-4 pb-4">
      <div>
        <TgSkeleton className="mb-2 h-7 w-48" />
        <TgSkeleton className="h-5 w-64" />
      </div>
      <div className="space-y-4">
        <TgSkeleton className="h-14 rounded-xl" />
        <TgSkeleton className="h-14 rounded-xl" />
        <TgSkeleton className="h-14 rounded-xl" />
        <TgSkeleton className="h-12 rounded-xl" />
        <TgSkeleton className="h-12 rounded-xl" />
        <TgSkeleton className="h-14 rounded-xl" />
        <TgSkeleton className="h-14 rounded-xl" />
        <TgSkeleton className="h-12 rounded-xl" />
      </div>
    </div>
  );
}

// ================================================================
// Shared Sub-components
// ================================================================

function FormField({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium">{label}</label>
      {children}
    </div>
  );
}

function SelectInput({
  value,
  onChange,
  placeholder,
  options,
  disabled,
}: {
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
  options: string[];
  disabled?: boolean;
}) {
  return (
    <div className="relative">
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        disabled={disabled}
        className={cn(
          "w-full min-h-[44px] appearance-none rounded-xl border border-slate-200 bg-white px-4 py-3 pr-10 text-sm focus:border-orange-500 focus:ring-2 focus:ring-orange-500 focus:outline-none",
          disabled && "cursor-not-allowed opacity-50",
          !value && "text-slate-400",
        )}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
      <ChevronDown className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
    </div>
  );
}
