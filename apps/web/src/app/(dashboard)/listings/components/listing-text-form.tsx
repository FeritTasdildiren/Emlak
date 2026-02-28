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
// Schema
// ---------------------------------------------------------------------------

const listingSchema = z.object({
  propertyType: z.enum(["daire", "villa", "ofis", "arsa", "dukkan"]),
  subCategory: z.string().optional(),
  roomCount: z.enum(["1+0", "1+1", "2+1", "3+1", "4+1", "5+2"]).optional(),
  grossSqm: z.coerce.number().min(1, "Metrekare giriniz"),
  netSqm: z.coerce.number().optional(),
  floor: z.coerce.number().optional(),
  totalFloors: z.coerce.number().optional(),
  buildingAge: z.coerce.number().min(0, "Yaş giriniz").optional(),
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
// Props
// ---------------------------------------------------------------------------

interface ListingTextFormProps {
  onSubmit: (data: ListingFormData) => void;
  isGenerating: boolean;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function ListingTextForm({ onSubmit, isGenerating }: ListingTextFormProps) {
  const { control, handleSubmit, watch, register, setValue } = useForm({
    resolver: zodResolver(listingSchema),
    defaultValues: {
      propertyType: "daire" as ExtendedPropertyType,
      subCategory: "",
      roomCount: "2+1" as const,
      grossSqm: 120,
      floor: 3,
      buildingAge: 5,
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

  // Oda sayisi gereken tipler
  const showRoomCount = selectedType === "daire" || selectedType === "villa" || selectedType === "ofis";
  const showFloor = selectedType !== "arsa";
  const showBuildingAge = selectedType !== "arsa";

  return (
    <form
      onSubmit={handleSubmit((data) => onSubmit(data as unknown as ListingFormData))}
      className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5 sm:p-6 space-y-6"
    >
      {/* 1. Property Type */}
      <fieldset>
        <legend className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
          Emlak Tipi
        </legend>
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
      </fieldset>

      {/* 1.5 Alt Kategori */}
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

      {/* 2. Features & Location */}
      <div className="grid sm:grid-cols-2 gap-6">
        <fieldset className="space-y-3">
          <legend className="text-sm font-semibold text-slate-900 dark:text-slate-200 border-b border-slate-100 dark:border-slate-800 pb-2 w-full">
            Özellikler
          </legend>
          <div className="grid grid-cols-2 gap-3">
            {showRoomCount && (
              <Controller
                name="roomCount"
                control={control}
                render={({ field }) => (
                  <Select
                    label="Oda Sayısı"
                    options={["1+0", "1+1", "2+1", "3+1", "4+1", "5+2"].map(
                      (v) => ({ value: v, label: v })
                    )}
                    value={field.value ?? ""}
                    onChange={(e) => field.onChange(e.target.value)}
                  />
                )}
              />
            )}
            <Input label="Brüt m²" type="number" {...register("grossSqm")} />
            {showFloor && (
              <Input
                label="Bulunduğu Kat"
                type="number"
                {...register("floor")}
              />
            )}
            {showBuildingAge && (
              <Input
                label="Bina Yaşı"
                type="number"
                {...register("buildingAge")}
              />
            )}
          </div>
        </fieldset>

        <fieldset className="space-y-3">
          <legend className="text-sm font-semibold text-slate-900 dark:text-slate-200 border-b border-slate-100 dark:border-slate-800 pb-2 w-full">
            Konum
          </legend>
          <div className="space-y-3">
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
      </div>

      {/* 3. Highlights — dinamik */}
      {visibleFeatures.length > 0 && (
        <fieldset>
          <legend className="block text-sm font-semibold text-slate-700 dark:text-slate-300 mb-3">
            Öne Çıkan Özellikler
          </legend>
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

      {/* 4. Notes */}
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

      {/* 5. Tone */}
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
