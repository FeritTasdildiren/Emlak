"use client"

import * as React from "react"
import { useForm, Controller } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { NumberInput } from "@/components/ui/number-input"
import { ValuationResult } from "./ValuationResult"
import { ComparablesList } from "./ComparablesList"
import { AreaComparison } from "./AreaComparison"
import { QuotaInfo } from "./QuotaInfo"
import { valuationSchema, type ValuationFormValues, type ValuationResultData } from "./schema"

import { submitValuation, getQuotaStatus } from "@/lib/api/valuations"

// ---------------------------------------------------------------------------
// Sub-components: SegmentedControl, Toggle, ChipSelect
// ---------------------------------------------------------------------------

interface SegmentedOption {
  value: string
  label: string
}

interface SegmentedControlProps {
  options: SegmentedOption[]
  value: string
  onChange: (value: string) => void
  label?: string
  className?: string
  error?: string
}

function SegmentedControl({ options, value, onChange, label, className, error }: SegmentedControlProps) {
  return (
    <div className={cn("space-y-2", className)}>
      {label && (
        <label className="text-sm font-medium leading-none text-zinc-900 dark:text-zinc-100">
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
              "rounded-md px-3 py-2 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600/20",
              "min-h-[40px] min-w-[44px]",
              value === opt.value
                ? "bg-orange-600 text-white shadow-sm"
                : "bg-zinc-100 text-zinc-700 hover:bg-zinc-200 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
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

interface ToggleProps {
  checked: boolean
  onChange: (checked: boolean) => void
  label: string
  className?: string
}

function Toggle({ checked, onChange, label, className }: ToggleProps) {
  return (
    <div className={cn("flex items-center justify-between", className)}>
      <label className="text-sm font-medium leading-none text-zinc-900 dark:text-zinc-100">
        {label}
      </label>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange(!checked)}
        className={cn(
          "relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600/20 focus-visible:ring-offset-2",
          checked ? "bg-orange-600" : "bg-zinc-300 dark:bg-zinc-600"
        )}
      >
        <span
          className={cn(
            "pointer-events-none inline-block h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform",
            checked ? "translate-x-5" : "translate-x-0"
          )}
        />
      </button>
    </div>
  )
}

interface RadioOption {
  value: string
  label: string
}

interface RadioGroupProps {
  options: RadioOption[]
  value: string
  onChange: (value: string) => void
  label?: string
  className?: string
  error?: string
}

function RadioGroup({ options, value, onChange, label, className, error }: RadioGroupProps) {
  return (
    <div className={cn("space-y-2", className)}>
      {label && (
        <label className="text-sm font-medium leading-none text-zinc-900 dark:text-zinc-100">
          {label}
        </label>
      )}
      <div className="flex gap-4">
        {options.map((opt) => (
          <label
            key={opt.value}
            onClick={() => onChange(opt.value)}
            className="flex cursor-pointer items-center gap-2 text-sm text-zinc-700 dark:text-zinc-300"
          >
            <span
              className={cn(
                "flex h-5 w-5 items-center justify-center rounded-full border-2 transition-colors",
                value === opt.value
                  ? "border-orange-600"
                  : "border-zinc-300 dark:border-zinc-600"
              )}
            >
              {value === opt.value && (
                <span className="h-2.5 w-2.5 rounded-full bg-orange-600" />
              )}
            </span>
            {opt.label}
          </label>
        ))}
      </div>
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  )
}

interface ChipOption {
  value: string
  label: string
}

interface ChipSelectProps {
  options: ChipOption[]
  value: string[]
  onChange: (value: string[]) => void
  label?: string
  className?: string
  error?: string
}

function ChipSelect({ options, value, onChange, label, className, error }: ChipSelectProps) {
  const toggle = (chipValue: string) => {
    if (value.includes(chipValue)) {
      onChange(value.filter((v) => v !== chipValue))
    } else {
      onChange([...value, chipValue])
    }
  }

  return (
    <div className={cn("space-y-2", className)}>
      {label && (
        <label className="text-sm font-medium leading-none text-zinc-900 dark:text-zinc-100">
          {label}
        </label>
      )}
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            onClick={() => toggle(opt.value)}
            className={cn(
              "rounded-full border px-3 py-1.5 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-orange-600/20",
              "min-h-[36px]",
              value.includes(opt.value)
                ? "border-orange-600 bg-orange-50 text-orange-700 dark:bg-orange-950 dark:text-orange-300"
                : "border-zinc-200 bg-white text-zinc-700 hover:border-zinc-300 hover:bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800 dark:text-zinc-300 dark:hover:bg-zinc-700"
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

// ---------------------------------------------------------------------------
// Section wrapper
// ---------------------------------------------------------------------------

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
      <legend className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
        {title}
      </legend>
      <div className="space-y-4">{children}</div>
    </fieldset>
  )
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const ilceler = [
  { value: "kadikoy", label: "Kadıköy" },
  { value: "besiktas", label: "Beşiktaş" },
  { value: "uskudar", label: "Üsküdar" },
  { value: "atasehir", label: "Ataşehir" },
  { value: "esenyurt", label: "Esenyurt" },
  { value: "bahcelievler", label: "Bahçelievler" },
  { value: "maltepe", label: "Maltepe" },
  { value: "pendik", label: "Pendik" },
  { value: "sariyer", label: "Sarıyer" },
  { value: "sisli", label: "Şişli" },
]

const mahalleler = [
  { value: "caferaga", label: "Caferağa" },
  { value: "moda", label: "Moda" },
  { value: "osmanaga", label: "Osmanağa" },
  { value: "fenerbahce", label: "Fenerbahçe" },
  { value: "goztepe", label: "Göztepe" },
  { value: "kozyatagi", label: "Kozyatağı" },
]

const katlar = [
  { value: "-1", label: "-1 (Bodrum)" },
  { value: "0", label: "0 (Zemin)" },
  ...Array.from({ length: 20 }, (_, i) => ({
    value: String(i + 1),
    label: String(i + 1),
  })),
  { value: "cati", label: "Çatı Katı" },
]

const isitmaTipleri = [
  { value: "dogalgaz-kombi", label: "Doğalgaz Kombi" },
  { value: "merkezi", label: "Merkezi Sistem" },
  { value: "klima", label: "Klima" },
  { value: "soba", label: "Soba" },
]

const mulkTipleri: SegmentedOption[] = [
  { value: "daire", label: "Daire" },
  { value: "villa", label: "Villa" },
  { value: "mustakil", label: "Müstakil" },
  { value: "isyeri", label: "İş Yeri" },
]

const odaSalonlar: SegmentedOption[] = [
  { value: "1+0", label: "1+0" },
  { value: "1+1", label: "1+1" },
  { value: "2+1", label: "2+1" },
  { value: "3+1", label: "3+1" },
  { value: "3+2", label: "3+2" },
  { value: "4+1", label: "4+1" },
  { value: "4+2", label: "4+2" },
  { value: "5+", label: "5+" },
]

const binaYaslari: SegmentedOption[] = [
  { value: "0-5", label: "0-5" },
  { value: "6-10", label: "6-10" },
  { value: "11-20", label: "11-20" },
  { value: "21-30", label: "21-30" },
  { value: "30+", label: "30+" },
]

const banyoSayilari: SegmentedOption[] = [
  { value: "1", label: "1" },
  { value: "2", label: "2" },
  { value: "3+", label: "3+" },
]

const otoparkSecenekleri: RadioOption[] = [
  { value: "acik", label: "Açık" },
  { value: "kapali", label: "Kapalı" },
  { value: "yok", label: "Yok" },
]

const cepheSecenekleri: ChipOption[] = [
  { value: "kuzey", label: "Kuzey" },
  { value: "guney", label: "Güney" },
  { value: "dogu", label: "Doğu" },
  { value: "bati", label: "Batı" },
]

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export interface ValuationFormProps {
  className?: string
}

export function ValuationForm({ className }: ValuationFormProps) {
  const [loading, setLoading] = React.useState(false)
  const [error, setError] = React.useState<string | null>(null)
  const [result, setResult] = React.useState<ValuationResultData | null>(null)
  const [quota, setQuota] = React.useState<{ remaining: number; limit: number } | null>(null)

  React.useEffect(() => {
    getQuotaStatus().then(setQuota).catch(console.error)
  }, [])

  const form = useForm({
    resolver: zodResolver(valuationSchema),
    defaultValues: {
      city: "istanbul",
      district: "",
      neighborhood: "",
      property_type: "daire",
      gross_sqm: undefined,
      net_sqm: undefined,
      room_count: "3+1",
      floor: "",
      building_age: "6-10",
      bathroom_count: "1",
      has_balcony: false,
      parking_type: "yok",
      has_elevator: false,
      heating_type: "",
      facades: [],
    },
  })

  const {
    control,
    handleSubmit,
    reset,
    formState: { errors },
  } = form

  const onSubmit = async (data: ValuationFormValues) => {
    setLoading(true)
    setError(null)
    setResult(null)
    
    try {
      const valuationResult = await submitValuation(data)
      setResult(valuationResult)
      // Update quota after successful valuation
      setQuota(prev => prev ? { ...prev, remaining: Math.max(0, prev.remaining - 1) } : null)
    } catch (err) {
      setError("Değerleme sırasında bir hata oluştu. Lütfen tekrar deneyiniz.")
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setResult(null)
    setError(null)
    reset()
  }

  const isQuotaExceeded = quota ? quota.remaining <= 0 : false

  return (
    <div className={cn("min-h-screen bg-zinc-50 dark:bg-zinc-950", className)}>
      <div className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            AI Değerleme
          </h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            Mülk bilgilerini girerek yapay zeka destekli fiyat tahmini alın.
          </p>
        </div>

        {/* Quota Exceeded Banner */}
        {isQuotaExceeded && (
          <div className="mb-8 rounded-md bg-red-50 p-4 border border-red-200 dark:bg-red-900/20 dark:border-red-800">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800 dark:text-red-200">Aylık değerleme limitinize ulaştınız.</h3>
                <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                  <p>Bu ay için belirlenen değerleme hakkınız dolmuştur. Daha fazla işlem yapabilmek için lütfen paketinizi yükseltin.</p>
                </div>
                <div className="mt-4">
                  <p className="text-xs text-red-600 dark:text-red-300">
                    Plan yükseltmek için <strong>destek@petqas.com</strong> adresine yazın.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Main Layout: Form + Result */}
        <div className="lg:flex lg:gap-8">
          {/* Form Panel */}
          <form
            onSubmit={handleSubmit(onSubmit)}
            className="flex-1 space-y-6 lg:max-w-2xl"
          >
            <fieldset disabled={isQuotaExceeded || loading} className="space-y-6 disabled:opacity-60">
            {/* Section 1: Konum Bilgileri */}
            <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm sm:p-6 dark:border-zinc-700 dark:bg-zinc-900">
              <FormSection title="Konum Bilgileri">
                <Controller
                  name="city"
                  control={control}
                  render={({ field }) => (
                    <Select
                      label="İl"
                      options={[{ value: "istanbul", label: "İstanbul" }]}
                      {...field}
                    />
                  )}
                />

                <div className="grid gap-4 sm:grid-cols-2">
                  <Controller
                    name="district"
                    control={control}
                    render={({ field }) => (
                      <Select
                        label="İlçe"
                        options={ilceler}
                        placeholder="İlçe seçin"
                        errorMessage={errors.district?.message}
                        {...field}
                      />
                    )}
                  />
                  <Controller
                    name="neighborhood"
                    control={control}
                    render={({ field }) => (
                      <Select
                        label="Mahalle"
                        options={mahalleler}
                        placeholder="Mahalle seçin"
                        errorMessage={errors.neighborhood?.message}
                        {...field}
                      />
                    )}
                  />
                </div>
              </FormSection>
            </div>

            {/* Section 2: Mülk Özellikleri */}
            <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm sm:p-6 dark:border-zinc-700 dark:bg-zinc-900">
              <FormSection title="Mülk Özellikleri">
                <Controller
                  name="property_type"
                  control={control}
                  render={({ field }) => (
                    <SegmentedControl
                      label="Mülk Tipi"
                      options={mulkTipleri}
                      value={field.value}
                      onChange={field.onChange}
                      error={errors.property_type?.message}
                    />
                  )}
                />

                <div className="grid gap-4 sm:grid-cols-2">
                  <Controller
                    name="gross_sqm"
                    control={control}
                    render={({ field }) => (
                      <NumberInput
                        label="Brüt m\u00B2"
                        suffix="m\u00B2"
                        placeholder="Örnek: 120"
                        min={10}
                        max={10000}
                        value={field.value}
                        onChange={field.onChange}
                        errorMessage={errors.gross_sqm?.message}
                      />
                    )}
                  />
                  <Controller
                    name="net_sqm"
                    control={control}
                    render={({ field }) => (
                      <NumberInput
                        label="Net m\u00B2"
                        suffix="m\u00B2"
                        placeholder="Örnek: 100"
                        min={10}
                        max={10000}
                        value={field.value}
                        onChange={field.onChange}
                        errorMessage={errors.net_sqm?.message}
                      />
                    )}
                  />
                </div>

                <Controller
                  name="room_count"
                  control={control}
                  render={({ field }) => (
                    <SegmentedControl
                      label="Oda + Salon"
                      options={odaSalonlar}
                      value={field.value}
                      onChange={field.onChange}
                      error={errors.room_count?.message}
                    />
                  )}
                />

                <div className="grid gap-4 sm:grid-cols-2">
                  <Controller
                    name="floor"
                    control={control}
                    render={({ field }) => (
                      <Select
                        label="Kat"
                        options={katlar}
                        placeholder="Kat seçin"
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
                      <SegmentedControl
                        label="Bina Yaşı"
                        options={binaYaslari}
                        value={field.value}
                        onChange={field.onChange}
                        error={errors.building_age?.message}
                      />
                    )}
                  />
                </div>
              </FormSection>
            </div>

            {/* Section 3: Ek Özellikler */}
            <div className="rounded-xl border border-zinc-200 bg-white p-4 shadow-sm sm:p-6 dark:border-zinc-700 dark:bg-zinc-900">
              <FormSection title="Ek Özellikler">
                <Controller
                  name="bathroom_count"
                  control={control}
                  render={({ field }) => (
                    <SegmentedControl
                      label="Banyo Sayısı"
                      options={banyoSayilari}
                      value={field.value}
                      onChange={field.onChange}
                      error={errors.bathroom_count?.message}
                    />
                  )}
                />

                <div className="grid gap-4 sm:grid-cols-2">
                  <Controller
                    name="has_balcony"
                    control={control}
                    render={({ field }) => (
                      <Toggle
                        label="Balkon"
                        checked={field.value}
                        onChange={field.onChange}
                      />
                    )}
                  />
                  <Controller
                    name="has_elevator"
                    control={control}
                    render={({ field }) => (
                      <Toggle
                        label="Asansör"
                        checked={field.value}
                        onChange={field.onChange}
                      />
                    )}
                  />
                </div>

                <Controller
                  name="parking_type"
                  control={control}
                  render={({ field }) => (
                    <RadioGroup
                      label="Otopark"
                      options={otoparkSecenekleri}
                      value={field.value}
                      onChange={field.onChange}
                      error={errors.parking_type?.message}
                    />
                  )}
                />

                <Controller
                  name="heating_type"
                  control={control}
                  render={({ field }) => (
                    <Select
                      label="Isıtma Tipi"
                      options={isitmaTipleri}
                      placeholder="Isıtma tipi seçin"
                      value={field.value}
                      onChange={field.onChange}
                      errorMessage={errors.heating_type?.message}
                    />
                  )}
                />

                <Controller
                  name="facades"
                  control={control}
                  render={({ field }) => (
                    <ChipSelect
                      label="Cephe Yönü"
                      options={cepheSecenekleri}
                      value={field.value || []}
                      onChange={field.onChange}
                      error={errors.facades?.message}
                    />
                  )}
                />
              </FormSection>
            </div>

            </fieldset>

            {/* Submit */}
            <Button
              type="submit"
              size="lg"
              fullWidth
              loading={loading}
              disabled={loading || isQuotaExceeded}
              className="bg-orange-600 text-white hover:bg-orange-700 focus-visible:ring-orange-600/20"
            >
              {loading ? "Değerleme yapılıyor..." : "Değerleme Yap"}
            </Button>
          </form>

          {/* Result Panel (Desktop: sticky sidebar / Mobile: below form) */}
          <div className="mt-8 lg:mt-0 lg:w-[400px] lg:shrink-0">
            <div className="lg:sticky lg:top-24 space-y-6">
              <ValuationResult 
                result={result} 
                loading={loading}
                error={error}
                onReset={handleReset} 
              />

              {result && (
                <>
                  <ComparablesList 
                    comparables={result.comparables} 
                    estimatedPrice={result.estimated_price} 
                  />
                  <AreaComparison 
                    listingPrice={result.estimated_price} 
                    areaAveragePrice={result.area_average_price || result.estimated_price} 
                  />
                  <QuotaInfo remaining={result.quota_remaining} limit={result.quota_limit} />
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
