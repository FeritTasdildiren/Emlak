"use client"

import * as React from "react"
import { useForm, Controller } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { NumberInput } from "@/components/ui/number-input"
import {
  fullPropertySchema,
  getPropertySchema,
  getTypeSpecificDefaults,
  type PropertyFormValues,
  type FormPropertyType,
} from "./property-form-schema"
import { toast } from "@/components/ui/toast"
import {
  cities,
  getDistrictsForCity,
  getSubCategories,
  type DetailedPropertyType,
} from "@/lib/location-data"

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface SegmentedOption {
  value: string
  label: string
}

function SegmentedControl({
  options,
  value,
  onChange,
  label,
  className,
  error,
}: {
  options: SegmentedOption[]
  value: string
  onChange: (value: string) => void
  label?: string
  className?: string
  error?: string
}) {
  return (
    <div className={cn("space-y-2", className)}>
      {label && (
        <label className="text-sm font-medium leading-none text-gray-900 dark:text-gray-100">
          {label}
        </label>
      )}
      <div className="flex flex-wrap gap-1.5">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => onChange(opt.value)}
            className={cn(
              "rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600/20",
              "min-h-[40px] min-w-[44px]",
              value === opt.value
                ? "bg-blue-600 text-white shadow-sm"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700"
            )}
          >
            {opt.label}
          </button>
        ))}
      </div>
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  )
}

function FormSection({
  title,
  children,
  className,
}: {
  title: string
  children: React.ReactNode
  className?: string
}) {
  return (
    <fieldset className={cn("space-y-4", className)}>
      <legend className="text-lg font-semibold text-gray-900 dark:text-gray-100">
        {title}
      </legend>
      <div className="space-y-4">{children}</div>
    </fieldset>
  )
}

function CheckboxField({
  label,
  checked,
  onChange,
}: {
  label: string
  checked: boolean
  onChange: (v: boolean) => void
}) {
  return (
    <label className="flex items-center gap-2.5 cursor-pointer group">
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="rounded border-gray-300 dark:border-gray-600 text-blue-600 focus:ring-blue-500 focus:ring-offset-0 h-4 w-4"
      />
      <span className="text-sm text-gray-700 dark:text-gray-300 group-hover:text-gray-900 dark:group-hover:text-gray-100 transition-colors">
        {label}
      </span>
    </label>
  )
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const listingTypes: SegmentedOption[] = [
  { value: "satilik", label: "Satılık" },
  { value: "kiralik", label: "Kiralık" },
]

const propertyTypes: SegmentedOption[] = [
  { value: "daire", label: "Daire" },
  { value: "villa", label: "Villa" },
  { value: "ofis", label: "Ofis" },
  { value: "arsa", label: "Arsa" },
  { value: "dukkan", label: "Dükkan" },
]

const roomOptions: SegmentedOption[] = [
  { value: "1+0", label: "1+0" },
  { value: "1+1", label: "1+1" },
  { value: "2+1", label: "2+1" },
  { value: "3+1", label: "3+1" },
  { value: "4+1", label: "4+1" },
  { value: "5+1", label: "5+1" },
  { value: "6+", label: "6+" },
]

const statusOptions: SegmentedOption[] = [
  { value: "draft", label: "Taslak" },
  { value: "active", label: "Aktif" },
]

const heatingOptions: SegmentedOption[] = [
  { value: "dogalgaz_kombi", label: "Doğalgaz Kombi" },
  { value: "merkezi", label: "Merkezi" },
  { value: "soba", label: "Soba" },
  { value: "klima", label: "Klima" },
  { value: "yerden_isitma", label: "Yerden Isıtma" },
]

const zoningOptions = [
  { value: "konut", label: "Konut İmarı" },
  { value: "ticari", label: "Ticari İmar" },
  { value: "karma", label: "Karma İmar" },
  { value: "sanayi", label: "Sanayi İmarı" },
  { value: "yok", label: "İmarsız" },
]

const infrastructureOptions = [
  { id: "elektrik", label: "Elektrik" },
  { id: "su", label: "Su" },
  { id: "dogalgaz", label: "Doğalgaz" },
  { id: "kanalizasyon", label: "Kanalizasyon" },
  { id: "yol", label: "Asfalt Yol" },
  { id: "internet", label: "Fiber İnternet" },
]

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

export interface PropertyFormProps {
  defaultValues?: Partial<PropertyFormValues>
  isEditing?: boolean
  onSubmit?: (data: PropertyFormValues) => void
  className?: string
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function PropertyForm({
  defaultValues,
  isEditing = false,
  onSubmit: onSubmitProp,
  className,
}: PropertyFormProps) {
  const [loading, setLoading] = React.useState(false)

  const form = useForm<PropertyFormValues>({
    resolver: zodResolver(fullPropertySchema),
    defaultValues: {
      title: "",
      property_type: "daire",
      sub_category: undefined,
      listing_type: "satilik",
      price: undefined,
      currency: "TRY",
      area_sqm: undefined,
      room_count: undefined,
      floor: undefined,
      total_floors: undefined,
      building_age: undefined,
      city: "",
      district: "",
      neighborhood: "",
      address: "",
      description: "",
      status: "draft",
      heating_type: undefined,
      has_balcony: false,
      has_elevator: false,
      has_parking: false,
      is_in_complex: false,
      is_furnished: false,
      has_pool: false,
      has_garden: false,
      has_garage: false,
      land_area: undefined,
      open_area: undefined,
      closed_area: undefined,
      has_meeting_room: false,
      zoning_status: undefined,
      floor_permission: undefined,
      taks: undefined,
      kaks: undefined,
      road_frontage: undefined,
      infrastructure: [],
      showcase_length: undefined,
      has_storage: false,
      ...defaultValues,
    },
  })

  const {
    control,
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = form

  const selectedPropertyType = watch("property_type") as FormPropertyType
  const selectedCity = watch("city")

  // Mulk tipi degisince tip-spesifik alanlari sifirla
  const prevTypeRef = React.useRef(selectedPropertyType)
  React.useEffect(() => {
    if (prevTypeRef.current !== selectedPropertyType) {
      const defaults = getTypeSpecificDefaults()
      const keys = Object.keys(defaults) as (keyof typeof defaults)[]
      for (const key of keys) {
        setValue(key, defaults[key])
      }
      prevTypeRef.current = selectedPropertyType
    }
  }, [selectedPropertyType, setValue])

  // Il degisince ilceyi sifirla
  const prevCityRef = React.useRef(selectedCity)
  React.useEffect(() => {
    if (prevCityRef.current !== selectedCity) {
      setValue("district", "")
      prevCityRef.current = selectedCity
    }
  }, [selectedCity, setValue])

  // Ilce listesi
  const districtOptions = React.useMemo(
    () => getDistrictsForCity(selectedCity),
    [selectedCity]
  )

  // Alt kategori listesi
  const subCategoryOptions = React.useMemo(
    () => getSubCategories(selectedPropertyType as DetailedPropertyType),
    [selectedPropertyType]
  )

  const onSubmit = async (data: PropertyFormValues) => {
    // Dinamik şema ile doğrula
    const schema = getPropertySchema(data.property_type as FormPropertyType)
    const result = schema.safeParse(data)
    if (!result.success) {
      const issues = "issues" in result.error ? (result.error as { issues: Array<{ message: string }> }).issues : []
      const firstMessage = issues[0]?.message
      toast(firstMessage ?? "Form doğrulama hatası")
      return
    }

    setLoading(true)
    try {
      if (onSubmitProp) {
        onSubmitProp(data)
      } else {
        console.log("Form verileri:", data)
        toast("Ilan basariyla kaydedildi!")
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className={cn("space-y-6", className)}
    >
      {/* Bolum 1: Temel Bilgiler */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 shadow-sm sm:p-6">
        <FormSection title="Temel Bilgiler">
          <Input
            label="İlan Başlığı"
            placeholder="Örn: Kadıköy Moda'da 3+1 Deniz Manzaralı Daire"
            errorMessage={errors.title?.message}
            {...register("title")}
          />

          <div className="grid gap-4 sm:grid-cols-2">
            <Controller
              name="listing_type"
              control={control}
              render={({ field }) => (
                <SegmentedControl
                  label="İlan Türü"
                  options={listingTypes}
                  value={field.value}
                  onChange={field.onChange}
                  error={errors.listing_type?.message}
                />
              )}
            />
            <Controller
              name="property_type"
              control={control}
              render={({ field }) => (
                <SegmentedControl
                  label="Mülk Tipi"
                  options={propertyTypes}
                  value={field.value}
                  onChange={field.onChange}
                  error={errors.property_type?.message}
                />
              )}
            />
          </div>

          {/* Alt Kategori */}
          {subCategoryOptions.length > 0 && (
            <Controller
              name="sub_category"
              control={control}
              render={({ field }) => (
                <Select
                  label="Alt Kategori"
                  options={subCategoryOptions}
                  placeholder="Alt kategori seçin"
                  value={field.value ?? ""}
                  onChange={(e) => field.onChange(e.target.value)}
                />
              )}
            />
          )}
        </FormSection>
      </div>

      {/* Bolum 2: Fiyat */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 shadow-sm sm:p-6">
        <FormSection title="Fiyat Bilgisi">
          <Controller
            name="price"
            control={control}
            render={({ field }) => (
              <NumberInput
                label="Fiyat"
                suffix="TL"
                placeholder="Örn: 5.000.000"
                min={1}
                value={field.value}
                onChange={field.onChange}
                errorMessage={errors.price?.message}
              />
            )}
          />
        </FormSection>
      </div>

      {/* Bolum 3: Mülk Özellikleri — dinamik */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 shadow-sm sm:p-6">
        <FormSection title="Mülk Özellikleri">
          {/* m2 — tum tipler */}
          <Controller
            name="area_sqm"
            control={control}
            render={({ field }) => (
              <NumberInput
                label="Alan (m²)"
                suffix="m²"
                placeholder="Örn: 120"
                min={1}
                max={50000}
                value={field.value}
                onChange={field.onChange}
                errorMessage={errors.area_sqm?.message}
              />
            )}
          />

          {/* -------- DAIRE ALANLARI -------- */}
          {selectedPropertyType === "daire" && (
            <>
              <Controller
                name="room_count"
                control={control}
                render={({ field }) => (
                  <SegmentedControl
                    label="Oda Sayısı"
                    options={roomOptions}
                    value={field.value ?? ""}
                    onChange={field.onChange}
                    error={errors.room_count?.message}
                  />
                )}
              />
              <div className="grid gap-4 sm:grid-cols-3">
                <Controller
                  name="floor"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Bulunduğu Kat"
                      placeholder="Örn: 3"
                      min={0}
                      max={100}
                      value={field.value}
                      onChange={field.onChange}
                      errorMessage={errors.floor?.message}
                    />
                  )}
                />
                <Controller
                  name="building_age"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Bina Yaşı"
                      placeholder="Örn: 5"
                      min={0}
                      max={100}
                      value={field.value}
                      onChange={field.onChange}
                      errorMessage={errors.building_age?.message}
                    />
                  )}
                />
                <Controller
                  name="heating_type"
                  control={control}
                  render={({ field }) => (
                    <SegmentedControl
                      label="Isıtma Tipi"
                      options={heatingOptions}
                      value={field.value ?? ""}
                      onChange={field.onChange}
                    />
                  )}
                />
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3 pt-2">
                <Controller name="has_balcony" control={control} render={({ field }) => (
                  <CheckboxField label="Balkon" checked={!!field.value} onChange={field.onChange} />
                )} />
                <Controller name="has_elevator" control={control} render={({ field }) => (
                  <CheckboxField label="Asansör" checked={!!field.value} onChange={field.onChange} />
                )} />
                <Controller name="has_parking" control={control} render={({ field }) => (
                  <CheckboxField label="Otopark" checked={!!field.value} onChange={field.onChange} />
                )} />
                <Controller name="is_in_complex" control={control} render={({ field }) => (
                  <CheckboxField label="Site İçi" checked={!!field.value} onChange={field.onChange} />
                )} />
                <Controller name="is_furnished" control={control} render={({ field }) => (
                  <CheckboxField label="Eşyalı" checked={!!field.value} onChange={field.onChange} />
                )} />
              </div>
            </>
          )}

          {/* -------- VILLA ALANLARI -------- */}
          {selectedPropertyType === "villa" && (
            <>
              <Controller
                name="room_count"
                control={control}
                render={({ field }) => (
                  <SegmentedControl
                    label="Oda Sayısı"
                    options={roomOptions}
                    value={field.value ?? ""}
                    onChange={field.onChange}
                    error={errors.room_count?.message}
                  />
                )}
              />
              <div className="grid gap-4 sm:grid-cols-3">
                <Controller
                  name="total_floors"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Kat Sayısı"
                      placeholder="Örn: 3"
                      min={1}
                      max={10}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  )}
                />
                <Controller
                  name="land_area"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Arsa Alanı (m²)"
                      placeholder="Örn: 500"
                      min={1}
                      max={100000}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  )}
                />
                <Controller
                  name="building_age"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Bina Yaşı"
                      placeholder="Örn: 5"
                      min={0}
                      max={100}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  )}
                />
              </div>
              <Controller
                name="heating_type"
                control={control}
                render={({ field }) => (
                  <SegmentedControl
                    label="Isıtma Tipi"
                    options={heatingOptions}
                    value={field.value ?? ""}
                    onChange={field.onChange}
                  />
                )}
              />
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
                <Controller name="has_pool" control={control} render={({ field }) => (
                  <CheckboxField label="Havuz" checked={!!field.value} onChange={field.onChange} />
                )} />
                <Controller name="has_garden" control={control} render={({ field }) => (
                  <CheckboxField label="Bahçe" checked={!!field.value} onChange={field.onChange} />
                )} />
                <Controller name="has_garage" control={control} render={({ field }) => (
                  <CheckboxField label="Garaj" checked={!!field.value} onChange={field.onChange} />
                )} />
              </div>
            </>
          )}

          {/* -------- OFIS ALANLARI -------- */}
          {selectedPropertyType === "ofis" && (
            <>
              <Controller
                name="room_count"
                control={control}
                render={({ field }) => (
                  <SegmentedControl
                    label="Oda Sayısı"
                    options={roomOptions}
                    value={field.value ?? ""}
                    onChange={field.onChange}
                  />
                )}
              />
              <div className="grid gap-4 sm:grid-cols-3">
                <Controller
                  name="floor"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Bulunduğu Kat"
                      placeholder="Örn: 5"
                      min={0}
                      max={100}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  )}
                />
                <Controller
                  name="building_age"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Bina Yaşı"
                      placeholder="Örn: 10"
                      min={0}
                      max={100}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  )}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <Controller
                  name="open_area"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Açık Alan (m²)"
                      placeholder="Örn: 50"
                      min={0}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  )}
                />
                <Controller
                  name="closed_area"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Kapalı Alan (m²)"
                      placeholder="Örn: 80"
                      min={0}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  )}
                />
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 pt-2">
                <Controller name="has_meeting_room" control={control} render={({ field }) => (
                  <CheckboxField label="Toplantı Odası" checked={!!field.value} onChange={field.onChange} />
                )} />
                <Controller name="has_elevator" control={control} render={({ field }) => (
                  <CheckboxField label="Asansör" checked={!!field.value} onChange={field.onChange} />
                )} />
                <Controller name="has_parking" control={control} render={({ field }) => (
                  <CheckboxField label="Otopark" checked={!!field.value} onChange={field.onChange} />
                )} />
              </div>
            </>
          )}

          {/* -------- ARSA ALANLARI -------- */}
          {selectedPropertyType === "arsa" && (
            <>
              <div className="grid gap-4 sm:grid-cols-2">
                <Controller
                  name="zoning_status"
                  control={control}
                  render={({ field }) => (
                    <Select
                      label="İmar Durumu"
                      options={zoningOptions}
                      placeholder="İmar durumu seçin"
                      value={field.value ?? ""}
                      onChange={(e) => field.onChange(e.target.value)}
                    />
                  )}
                />
                <Controller
                  name="floor_permission"
                  control={control}
                  render={({ field }) => (
                    <Input
                      label="Kat İzni"
                      placeholder="Örn: 5 kat"
                      value={field.value ?? ""}
                      onChange={field.onChange}
                    />
                  )}
                />
              </div>
              <div className="grid gap-4 sm:grid-cols-3">
                <Controller
                  name="taks"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="TAKS"
                      placeholder="Örn: 0.40"
                      min={0}
                      max={1}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  )}
                />
                <Controller
                  name="kaks"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="KAKS"
                      placeholder="Örn: 2.07"
                      min={0}
                      max={10}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  )}
                />
                <Controller
                  name="road_frontage"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Yola Cephe (m)"
                      placeholder="Örn: 20"
                      min={0}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  )}
                />
              </div>
              {/* Altyapi coklu secim */}
              <div>
                <label className="text-sm font-medium leading-none text-gray-900 dark:text-gray-100 mb-2 block">
                  Altyapı
                </label>
                <Controller
                  name="infrastructure"
                  control={control}
                  render={({ field }) => (
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                      {infrastructureOptions.map((opt) => {
                        const current = field.value ?? []
                        const isChecked = current.includes(opt.id)
                        return (
                          <CheckboxField
                            key={opt.id}
                            label={opt.label}
                            checked={isChecked}
                            onChange={(checked) => {
                              if (checked) {
                                field.onChange([...current, opt.id])
                              } else {
                                field.onChange(current.filter((v: string) => v !== opt.id))
                              }
                            }}
                          />
                        )
                      })}
                    </div>
                  )}
                />
              </div>
            </>
          )}

          {/* -------- DUKKAN ALANLARI -------- */}
          {selectedPropertyType === "dukkan" && (
            <>
              <div className="grid gap-4 sm:grid-cols-3">
                <Controller
                  name="floor"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Bulunduğu Kat"
                      placeholder="Örn: 0 (zemin)"
                      min={-5}
                      max={100}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  )}
                />
                <Controller
                  name="showcase_length"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Vitrin Uzunluğu (m)"
                      placeholder="Örn: 8"
                      min={0}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  )}
                />
                <Controller
                  name="building_age"
                  control={control}
                  render={({ field }) => (
                    <NumberInput
                      label="Bina Yaşı"
                      placeholder="Örn: 10"
                      min={0}
                      max={100}
                      value={field.value}
                      onChange={field.onChange}
                    />
                  )}
                />
              </div>
              <Controller name="has_storage" control={control} render={({ field }) => (
                <CheckboxField label="Depo Var" checked={!!field.value} onChange={field.onChange} />
              )} />
            </>
          )}
        </FormSection>
      </div>

      {/* Bolum 4: Konum */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 shadow-sm sm:p-6">
        <FormSection title="Konum Bilgileri">
          <div className="grid gap-4 sm:grid-cols-2">
            <Controller
              name="city"
              control={control}
              render={({ field }) => (
                <Select
                  label="Şehir"
                  options={cities}
                  placeholder="Şehir seçin"
                  errorMessage={errors.city?.message}
                  value={field.value}
                  onChange={(e) => field.onChange(e.target.value)}
                />
              )}
            />
            <Controller
              name="district"
              control={control}
              render={({ field }) => (
                <Select
                  label="İlçe"
                  options={districtOptions}
                  placeholder={selectedCity ? "İlçe seçin" : "Önce şehir seçin"}
                  errorMessage={errors.district?.message}
                  disabled={!selectedCity}
                  value={field.value}
                  onChange={(e) => field.onChange(e.target.value)}
                />
              )}
            />
          </div>

          <Input
            label="Mahalle"
            placeholder="Mahalle adı (opsiyonel)"
            errorMessage={errors.neighborhood?.message}
            {...register("neighborhood")}
          />

          <div className="space-y-2">
            <label className="text-sm font-medium leading-none text-gray-900 dark:text-gray-100">
              Adres
            </label>
            <textarea
              placeholder="Detaylı adres bilgisi (opsiyonel)"
              rows={2}
              className={cn(
                "flex w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-none",
                errors.address && "border-red-500 focus-visible:ring-red-500"
              )}
              {...register("address")}
            />
            {errors.address && (
              <p className="text-sm text-red-500">{errors.address.message}</p>
            )}
          </div>
        </FormSection>
      </div>

      {/* Bolum 5: Aciklama */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 shadow-sm sm:p-6">
        <FormSection title="Açıklama">
          <div className="space-y-2">
            <label className="text-sm font-medium leading-none text-gray-900 dark:text-gray-100">
              Detaylı Açıklama
            </label>
            <textarea
              placeholder="Mülk hakkında detaylı bilgi yazın (opsiyonel)"
              rows={5}
              className={cn(
                "flex w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y",
                errors.description &&
                  "border-red-500 focus-visible:ring-red-500"
              )}
              {...register("description")}
            />
            {errors.description && (
              <p className="text-sm text-red-500">
                {errors.description.message}
              </p>
            )}
          </div>
        </FormSection>
      </div>

      {/* Bolum 6: Durum */}
      <div className="rounded-xl border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 p-4 shadow-sm sm:p-6">
        <FormSection title="İlan Durumu">
          <Controller
            name="status"
            control={control}
            render={({ field }) => (
              <SegmentedControl
                options={statusOptions}
                value={field.value}
                onChange={field.onChange}
                error={errors.status?.message}
              />
            )}
          />
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Taslak olarak kaydedilen ilanlar yayınlanmaz.
          </p>
        </FormSection>
      </div>

      {/* Submit */}
      <Button type="submit" size="lg" fullWidth loading={loading}>
        {loading
          ? "Kaydediliyor..."
          : isEditing
            ? "İlanı Güncelle"
            : "İlan Oluştur"}
      </Button>
    </form>
  )
}
