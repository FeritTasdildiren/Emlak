"use client";

import * as React from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import { ListingFormData, ToneType, PropertyType } from "@/types/listing";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import {
  Home,
  Castle,
  Briefcase,
  Map as MapIcon,
  Store,
  Sparkles,
  Building,
  Heart,
  Flame,
} from "lucide-react";
import { cn } from "@/lib/utils";
import {
  cities,
  getDistrictsForCity,
  getSubCategories,
  type DetailedPropertyType,
} from "@/lib/location-data";

// ---------------------------------------------------------------------------
// Genisletilmis property type (dukkan dahil)
// ---------------------------------------------------------------------------

type ExtendedPropertyType = PropertyType | "dukkan";

// ---------------------------------------------------------------------------
// Select secenekleri
// ---------------------------------------------------------------------------

const ROOM_COUNT_OPTIONS = [
  "1+0", "1+1", "2+0", "2+1", "2+2", "3+0", "3+1", "3+2",
  "4+1", "4+2", "5+1", "5+2", "6+1", "6+2", "7+",
].map((v) => ({ value: v, label: v }));

const BATHROOM_COUNT_OPTIONS = [
  { value: "1", label: "1" },
  { value: "2", label: "2" },
  { value: "3", label: "3" },
  { value: "4", label: "4" },
  { value: "5+", label: "5+" },
];

const FLOOR_INFO_OPTIONS = [
  { value: "bodrum", label: "Bodrum" },
  { value: "zemin_kat", label: "Zemin Kat" },
  { value: "giris_kat", label: "Giriş Kat" },
  { value: "ara_kat", label: "Ara Kat" },
  { value: "en_ust_kat", label: "En Üst Kat" },
  { value: "dublex", label: "Dubleks" },
  { value: "triplex", label: "Tripleks" },
  { value: "cati_kati", label: "Çatı Katı" },
];

const HEATING_TYPE_OPTIONS = [
  { value: "dogalgaz_kombi", label: "Doğalgaz (Kombi)" },
  { value: "dogalgaz_merkezi", label: "Doğalgaz (Merkezi)" },
  { value: "merkezi_pay_olcer", label: "Merkezi (Pay Ölçer)" },
  { value: "klima", label: "Klima" },
  { value: "soba", label: "Soba" },
  { value: "yerden_isitma", label: "Yerden Isıtma" },
  { value: "yok", label: "Yok" },
];

const FURNITURE_STATUS_OPTIONS = [
  { value: "bos", label: "Boş" },
  { value: "esyali", label: "Eşyalı" },
  { value: "yari_esyali", label: "Yarı Eşyalı" },
];

const FACADE_OPTIONS = [
  { value: "kuzey", label: "Kuzey" },
  { value: "guney", label: "Güney" },
  { value: "dogu", label: "Doğu" },
  { value: "bati", label: "Batı" },
  { value: "kuzey_dogu", label: "Kuzey-Doğu" },
  { value: "kuzey_bati", label: "Kuzey-Batı" },
  { value: "guney_dogu", label: "Güney-Doğu" },
  { value: "guney_bati", label: "Güney-Batı" },
];

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const listingSchema = z.object({
  propertyType: z.enum(["daire", "villa", "ofis", "arsa", "dukkan"]),
  subCategory: z.string().optional(),
  roomCount: z.enum(["1+0", "1+1", "2+0", "2+1", "2+2", "3+0", "3+1", "3+2", "4+1", "4+2", "5+1", "5+2", "6+1", "6+2", "7+"]).optional(),
  bathroomCount: z.enum(["1", "2", "3", "4", "5+"]).optional(),
  grossSqm: z.coerce.number().min(1, "Metrekare giriniz"),
  netSqm: z.coerce.number().optional(),
  price: z.coerce.number().min(1, "Fiyat zorunludur"),
  floor: z.coerce.number().optional(),
  totalFloors: z.coerce.number().optional(),
  buildingAge: z.coerce.number().min(0, "Yaş giriniz").max(100, "Maksimum 100").optional(),
  floorInfo: z.enum(["bodrum", "zemin_kat", "giris_kat", "ara_kat", "en_ust_kat", "dublex", "triplex", "cati_kati"]).optional(),
  heatingType: z.enum(["dogalgaz_kombi", "dogalgaz_merkezi", "merkezi_pay_olcer", "klima", "soba", "yerden_isitma", "yok"]).optional(),
  furnitureStatus: z.enum(["bos", "esyali", "yari_esyali"]).optional(),
  facade: z.enum(["kuzey", "guney", "dogu", "bati", "kuzey_dogu", "kuzey_bati", "guney_dogu", "guney_bati"]).optional(),
  city: z.string().min(1, "İl seçiniz"),
  district: z.string().min(1, "İlçe seçiniz"),
  neighborhood: z.string().optional(),
  features: z.object({
    balcony: z.boolean(),
    parking: z.boolean(),
    security: z.boolean(),
    pool: z.boolean(),
    seaView: z.boolean(),
    centralHeating: z.boolean(),
    elevator: z.boolean(),
    metroNearby: z.boolean(),
  }),
  additionalNotes: z.string(),
  tone: z.enum(["kurumsal", "samimi", "acil"]),
});

// ---------------------------------------------------------------------------
// Feature tanimlari — mulk tipine gore
// ---------------------------------------------------------------------------

const featuresByType: Record<ExtendedPropertyType, { id: string; label: string }[]> = {
  daire: [
    { id: "balcony", label: "Balkon" },
    { id: "parking", label: "Otopark" },
    { id: "security", label: "Güvenlik" },
    { id: "seaView", label: "Deniz Manzarası" },
    { id: "centralHeating", label: "Merkezi Isıtma" },
    { id: "elevator", label: "Asansör" },
    { id: "metroNearby", label: "Metro Yakını" },
  ],
  villa: [
    { id: "pool", label: "Havuz" },
    { id: "parking", label: "Garaj" },
    { id: "security", label: "Güvenlik" },
    { id: "seaView", label: "Deniz Manzarası" },
    { id: "centralHeating", label: "Merkezi Isıtma" },
  ],
  ofis: [
    { id: "parking", label: "Otopark" },
    { id: "security", label: "Güvenlik" },
    { id: "elevator", label: "Asansör" },
    { id: "centralHeating", label: "Klima" },
    { id: "metroNearby", label: "Metro Yakını" },
  ],
  arsa: [
    { id: "metroNearby", label: "Ulaşım Yakını" },
  ],
  dukkan: [
    { id: "parking", label: "Otopark" },
    { id: "security", label: "Güvenlik" },
    { id: "elevator", label: "Asansör" },
    { id: "metroNearby", label: "Metro Yakını" },
  ],
};

// ---------------------------------------------------------------------------
// Bolum basligi yardimci bileseni
// ---------------------------------------------------------------------------

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200 border-b border-slate-100 dark:border-slate-800 pb-2">
      {children}
    </h3>
  );
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ListingTextFormProps {
  onSubmit: (data: ListingFormData) => void;
  isGenerating: boolean;
  initialData?: Partial<ListingFormData>;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ListingTextForm({ onSubmit, isGenerating, initialData }: ListingTextFormProps) {
  const { control, handleSubmit, watch, register, setValue, reset } = useForm({
    resolver: zodResolver(listingSchema),
    defaultValues: {
      propertyType: "daire" as ExtendedPropertyType,
      subCategory: "",
      roomCount: "3+1" as const,
      bathroomCount: undefined as "1" | "2" | "3" | "4" | "5+" | undefined,
      grossSqm: 120,
      netSqm: undefined as number | undefined,
      price: 0,
      floor: undefined as number | undefined,
      totalFloors: undefined as number | undefined,
      buildingAge: undefined as number | undefined,
      floorInfo: undefined as "bodrum" | "zemin_kat" | "giris_kat" | "ara_kat" | "en_ust_kat" | "dublex" | "triplex" | "cati_kati" | undefined,
      heatingType: undefined as "dogalgaz_kombi" | "dogalgaz_merkezi" | "merkezi_pay_olcer" | "klima" | "soba" | "yerden_isitma" | "yok" | undefined,
      furnitureStatus: undefined as "bos" | "esyali" | "yari_esyali" | undefined,
      facade: undefined as "kuzey" | "guney" | "dogu" | "bati" | "kuzey_dogu" | "kuzey_bati" | "guney_dogu" | "guney_bati" | undefined,
      city: "",
      district: "",
      neighborhood: "",
      features: {
        balcony: true,
        parking: false,
        security: false,
        pool: false,
        seaView: false,
        centralHeating: true,
        elevator: true,
        metroNearby: false,
      },
      additionalNotes: "",
      tone: "kurumsal" as ToneType,
    },
  });

  // initialData degisince formu guncelle
  React.useEffect(() => {
    if (initialData) {
      // Mevcut default'lari koruyarak uzerine yaz
      reset((prev) => ({
        ...prev,
        ...initialData,
        // features nesne oldugu icin ozel ele almak gerekebilir ama Partial<ListingFormData> ise yeterli olabilir
        features: {
          ...prev.features,
          ...(initialData.features || {}),
        }
      }));
    }
  }, [initialData, reset]);

  const selectedTone = watch("tone") as ToneType;
  const selectedType = watch("propertyType") as ExtendedPropertyType;
  const selectedCity = watch("city");

  // Il degisince ilceyi sifirla
  const prevCityRef = React.useRef(selectedCity);
  React.useEffect(() => {
    if (prevCityRef.current !== selectedCity) {
      setValue("district", "");
      prevCityRef.current = selectedCity;
    }
  }, [selectedCity, setValue]);

  // Ilce listesi
  const districtOptions = React.useMemo(
    () => getDistrictsForCity(selectedCity),
    [selectedCity]
  );

  // Alt kategori listesi
  const subCategoryOptions = React.useMemo(
    () => getSubCategories(selectedType as DetailedPropertyType),
    [selectedType]
  );

  // Tip icin uygun feature'lar
  const visibleFeatures = featuresByType[selectedType] ?? [];

  // Arsa disindakiler icin gorunurluk kontrolleri
  const isNotArsa = selectedType !== "arsa";
  const showRoomCount = selectedType === "daire" || selectedType === "villa" || selectedType === "ofis";

  return (
    <form
      onSubmit={handleSubmit((data) => onSubmit(data as unknown as ListingFormData))}
      className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5 sm:p-6 space-y-6"
    >
      {/* ================================================================= */}
      {/* BOLUM 1: Temel Bilgiler                                          */}
      {/* ================================================================= */}
      <fieldset className="space-y-4">
        <SectionHeading>Temel Bilgiler</SectionHeading>

        {/* Emlak Tipi — radio card */}
        <div>
          <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">
            Emlak Tipi
          </label>
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
            {[
              { value: "daire", label: "Daire", icon: Home },
              { value: "villa", label: "Villa", icon: Castle },
              { value: "ofis", label: "Ofis", icon: Briefcase },
              { value: "arsa", label: "Arsa", icon: MapIcon },
              { value: "dukkan", label: "Dükkan", icon: Store },
            ].map((type) => (
              <label key={type.value} className="cursor-pointer">
                <input
                  type="radio"
                  value={type.value}
                  {...register("propertyType")}
                  className="peer sr-only"
                />
                <div
                  className={cn(
                    "p-3 sm:p-4 rounded-lg border-2 transition-all text-center",
                    selectedType === type.value
                      ? "border-indigo-600 bg-indigo-50 dark:bg-indigo-900/30"
                      : "border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800"
                  )}
                >
                  <type.icon
                    className={cn(
                      "w-6 h-6 mx-auto mb-1.5",
                      selectedType === type.value
                        ? "text-indigo-600 dark:text-indigo-400"
                        : "text-slate-400 dark:text-slate-500"
                    )}
                  />
                  <span
                    className={cn(
                      "text-sm font-medium",
                      selectedType === type.value
                        ? "text-indigo-700 dark:text-indigo-300"
                        : "text-slate-600 dark:text-slate-400"
                    )}
                  >
                    {type.label}
                  </span>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Alt Kategori */}
        {subCategoryOptions.length > 0 && (
          <Controller
            name="subCategory"
            control={control}
            render={({ field }) => (
              <Select
                label="Alt Kategori"
                options={subCategoryOptions}
                placeholder="Alt kategori seçin (opsiyonel)"
                value={field.value ?? ""}
                onChange={(e) => field.onChange(e.target.value)}
              />
            )}
          />
        )}

        {/* Fiyat + Konum — grid */}
        <div className="grid sm:grid-cols-2 gap-4">
          <Input
            label="Fiyat (₺)"
            type="number"
            placeholder="Satış fiyatı"
            {...register("price")}
          />
          {/* Il secimi */}
          <Controller
            name="city"
            control={control}
            render={({ field }) => (
              <Select
                label="İl"
                options={cities}
                placeholder="İl seçin"
                value={field.value}
                onChange={(e) => field.onChange(e.target.value)}
              />
            )}
          />
        </div>

        <div className="grid sm:grid-cols-2 gap-4">
          {/* Ilce secimi */}
          <Controller
            name="district"
            control={control}
            render={({ field }) => (
              <Select
                label="İlçe"
                options={districtOptions}
                placeholder={selectedCity ? "İlçe seçin" : "Önce il seçin"}
                disabled={!selectedCity}
                value={field.value}
                onChange={(e) => field.onChange(e.target.value)}
              />
            )}
          />
          <Input
            label="Mahalle (opsiyonel)"
            placeholder="Örn: Moda, Caferağa..."
            {...register("neighborhood")}
          />
        </div>
      </fieldset>

      {/* ================================================================= */}
      {/* BOLUM 2: Fiziksel Ozellikler                                      */}
      {/* ================================================================= */}
      <fieldset className="space-y-4">
        <SectionHeading>Fiziksel Özellikler</SectionHeading>

        <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
          {/* Oda Sayisi */}
          {showRoomCount && (
            <Controller
              name="roomCount"
              control={control}
              render={({ field }) => (
                <Select
                  label="Oda Sayısı"
                  options={ROOM_COUNT_OPTIONS}
                  placeholder="Seçin"
                  value={field.value ?? ""}
                  onChange={(e) => field.onChange(e.target.value)}
                />
              )}
            />
          )}

          {/* Banyo Sayisi — arsa haric */}
          {isNotArsa && (
            <Controller
              name="bathroomCount"
              control={control}
              render={({ field }) => (
                <Select
                  label="Banyo Sayısı"
                  options={BATHROOM_COUNT_OPTIONS}
                  placeholder="Seçin"
                  value={field.value ?? ""}
                  onChange={(e) => field.onChange(e.target.value)}
                />
              )}
            />
          )}

          {/* Brut m2 */}
          <Input label="Brüt m²" type="number" {...register("grossSqm")} />

          {/* Net m2 */}
          <Input label="Net m²" type="number" {...register("netSqm")} />

          {/* Kat Bilgisi — arsa haric */}
          {isNotArsa && (
            <Controller
              name="floorInfo"
              control={control}
              render={({ field }) => (
                <Select
                  label="Kat Bilgisi"
                  options={FLOOR_INFO_OPTIONS}
                  placeholder="Seçin"
                  value={field.value ?? ""}
                  onChange={(e) => field.onChange(e.target.value)}
                />
              )}
            />
          )}

          {/* Bina Yasi — arsa haric */}
          {isNotArsa && (
            <Input
              label="Bina Yaşı (yıl)"
              type="number"
              min={0}
              max={100}
              {...register("buildingAge")}
            />
          )}
        </div>
      </fieldset>

      {/* ================================================================= */}
      {/* BOLUM 3: Ek Bilgiler — arsa haric                                */}
      {/* ================================================================= */}
      {isNotArsa && (
        <fieldset className="space-y-4">
          <SectionHeading>Ek Bilgiler</SectionHeading>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {/* Isitma Tipi */}
            <Controller
              name="heatingType"
              control={control}
              render={({ field }) => (
                <Select
                  label="Isıtma Tipi"
                  options={HEATING_TYPE_OPTIONS}
                  placeholder="Seçin"
                  value={field.value ?? ""}
                  onChange={(e) => field.onChange(e.target.value)}
                />
              )}
            />

            {/* Esya Durumu */}
            <Controller
              name="furnitureStatus"
              control={control}
              render={({ field }) => (
                <Select
                  label="Eşya Durumu"
                  options={FURNITURE_STATUS_OPTIONS}
                  placeholder="Seçin"
                  value={field.value ?? ""}
                  onChange={(e) => field.onChange(e.target.value)}
                />
              )}
            />

            {/* Cephe */}
            <Controller
              name="facade"
              control={control}
              render={({ field }) => (
                <Select
                  label="Cephe"
                  options={FACADE_OPTIONS}
                  placeholder="Seçin"
                  value={field.value ?? ""}
                  onChange={(e) => field.onChange(e.target.value)}
                />
              )}
            />
          </div>
        </fieldset>
      )}

      {/* ================================================================= */}
      {/* BOLUM 4: One Cikan Ozellikler (checkbox) — DEGISTIRILMEDI        */}
      {/* ================================================================= */}
      {visibleFeatures.length > 0 && (
        <fieldset className="space-y-3">
          <SectionHeading>Öne Çıkan Özellikler</SectionHeading>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {visibleFeatures.map((item) => (
              <label
                key={item.id}
                className="inline-flex items-center gap-2 cursor-pointer"
              >
                <input
                  type="checkbox"
                  // eslint-disable-next-line @typescript-eslint/no-explicit-any
                  {...register(`features.${item.id}` as any)}
                  className="rounded border-slate-300 dark:border-slate-600 text-indigo-600 focus:ring-indigo-500 focus:ring-offset-0"
                />
                <span className="text-sm text-slate-600 dark:text-slate-400">
                  {item.label}
                </span>
              </label>
            ))}
          </div>
        </fieldset>
      )}

      {/* ================================================================= */}
      {/* Ek Notlar                                                         */}
      {/* ================================================================= */}
      <div>
        <label className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-2">
          Ek Notlar
        </label>
        <textarea
          rows={3}
          {...register("additionalNotes")}
          className="block w-full rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-slate-800 text-slate-900 dark:text-slate-100 shadow-sm focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 text-sm py-2.5 px-3 placeholder-slate-400 dark:placeholder-slate-500 resize-none"
          placeholder="Örn: Yeni tadilattan çıktı, açık mutfak, ebeveyn banyosu mevcut..."
        />
        <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">
          İlanda vurgulanmasını istediğiniz detayları buraya yazın.
        </p>
      </div>

      {/* ================================================================= */}
      {/* BOLUM 5: Ton                                                      */}
      {/* ================================================================= */}
      <fieldset>
        <legend className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
          İlan Dili / Tonu
        </legend>
        <div className="bg-slate-100 dark:bg-slate-800 p-1 rounded-lg flex">
          {[
            { value: "kurumsal", label: "Kurumsal" },
            { value: "samimi", label: "Samimi" },
            { value: "acil", label: "Acil / Fırsat" },
          ].map((tone) => (
            <button
              key={tone.value}
              type="button"
              onClick={() => setValue("tone", tone.value as ToneType)}
              className={cn(
                "flex-1 py-2.5 px-3 rounded-md text-sm font-medium transition-all",
                selectedTone === tone.value
                  ? "bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-slate-100"
                  : "text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200"
              )}
            >
              {tone.label}
            </button>
          ))}
        </div>

        <div className="mt-3">
          {selectedTone === "kurumsal" && (
            <div className="flex items-start gap-2 p-3 bg-indigo-50 dark:bg-indigo-900/20 rounded-lg border border-indigo-100 dark:border-indigo-800/50">
              <Building className="w-4 h-4 text-indigo-600 dark:text-indigo-400 mt-0.5 shrink-0" />
              <p className="text-xs text-indigo-700 dark:text-indigo-300">
                Profesyonel ve resmi dil. Kurumsal alıcılara, yatırımcılara
                hitap eder. Teknik detaylar ön plandadır.
              </p>
            </div>
          )}
          {selectedTone === "samimi" && (
            <div className="flex items-start gap-2 p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg border border-amber-100 dark:border-amber-800/50">
              <Heart className="w-4 h-4 text-amber-600 dark:text-amber-400 mt-0.5 shrink-0" />
              <p className="text-xs text-amber-700 dark:text-amber-300">
                Sıcak, samimi bir anlatım. Aile arayan bireysel alıcılara hitap
                eder. Yaşam alanı vurgusu yapılır.
              </p>
            </div>
          )}
          {selectedTone === "acil" && (
            <div className="flex items-start gap-2 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-100 dark:border-red-800/50">
              <Flame className="w-4 h-4 text-red-600 dark:text-red-400 mt-0.5 shrink-0" />
              <p className="text-xs text-red-700 dark:text-red-300">
                Aciliyet hissi veren, fırsat vurgulayan dil. Hızlı satış hedefi
                olan ilanlar için idealdir.
              </p>
            </div>
          )}
        </div>
      </fieldset>

      {/* ================================================================= */}
      {/* Submit                                                            */}
      {/* ================================================================= */}
      <div className="pt-2 border-t border-slate-100 dark:border-slate-800">
        <Button
          type="submit"
          disabled={isGenerating}
          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-6"
        >
          {isGenerating ? (
            <span className="flex items-center gap-2">
              <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
              Oluşturuluyor...
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <Sparkles className="w-5 h-5" />
              İlan Metni Oluştur
            </span>
          )}
        </Button>
        <p className="mt-2 text-center text-xs text-slate-400 dark:text-slate-500">
          1 kredi kullanılır
        </p>
      </div>
    </form>
  );
}
