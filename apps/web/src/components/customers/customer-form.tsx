"use client"

import * as React from "react"
import { useForm, Controller } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Select } from "@/components/ui/select"
import { NumberInput } from "@/components/ui/number-input"

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const customerFormSchema = z.object({
  full_name: z.string().min(2, "Ad soyad en az 2 karakter olmalıdır"),
  phone: z.string().optional(),
  email: z.string().email("Geçerli bir e-posta adresi giriniz").optional().or(z.literal("")),
  customer_type: z.enum(["buyer", "seller", "renter", "landlord"] as const),
  source: z.string().optional(),
  budget_min: z.number().optional(),
  budget_max: z.number().optional(),
  desired_rooms: z.string().optional(),
  desired_area_min: z.number().optional(),
  desired_area_max: z.number().optional(),
  desired_districts: z.array(z.string()),
  tags: z.array(z.string()),
  notes: z.string().optional(),
  gender: z.string().optional(),
  age_range: z.string().optional(),
  profession: z.string().optional(),
  family_size: z.number().min(1).max(10).optional(),
})

export type CustomerFormValues = z.infer<typeof customerFormSchema>

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
        <label className="text-sm font-medium leading-none text-gray-900">
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
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
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
      <legend className="text-lg font-semibold text-gray-900">{title}</legend>
      <div className="space-y-4">{children}</div>
    </fieldset>
  )
}

function TagInput({
  value = [],
  onChange,
  label,
  placeholder = "Etiket eklemek için yazıp Enter'a basın",
  error,
}: {
  value: string[]
  onChange: (tags: string[]) => void
  label?: string
  placeholder?: string
  error?: string
}) {
  const [inputValue, setInputValue] = React.useState("")

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.preventDefault()
      const trimmed = inputValue.trim()
      if (trimmed && !value.includes(trimmed)) {
        onChange([...value, trimmed])
        setInputValue("")
      }
    }
  }

  const removeTag = (tagToRemove: string) => {
    onChange(value.filter((tag) => tag !== tagToRemove))
  }

  return (
    <div className="space-y-2">
      {label && (
        <label className="text-sm font-medium leading-none text-gray-900">
          {label}
        </label>
      )}
      <div className="flex flex-wrap gap-2 mb-2">
        {value.map((tag) => (
          <span
            key={tag}
            className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800"
          >
            {tag}
            <button
              type="button"
              onClick={() => removeTag(tag)}
              className="ml-1.5 inline-flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-blue-600 hover:bg-blue-200 hover:text-blue-900 focus:bg-blue-500 focus:text-white focus:outline-none"
            >
              <span className="sr-only">Etiketi kaldır</span>
              <X className="h-3 w-3" />
            </button>
          </span>
        ))}
      </div>
      <Input
        value={inputValue}
        onChange={(e) => setInputValue(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
      />
      {error && <p className="text-sm text-red-500">{error}</p>}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const customerTypes: SegmentedOption[] = [
  { value: "buyer", label: "Alıcı" },
  { value: "seller", label: "Satıcı" },
  { value: "renter", label: "Kiracı" },
  { value: "landlord", label: "Ev Sahibi" },
]

const sources = [
  { value: "manual", label: "Manuel Giriş" },
  { value: "web", label: "Web Sitesi" },
  { value: "whatsapp", label: "WhatsApp" },
  { value: "telegram", label: "Telegram" },
  { value: "referral", label: "Referans" },
]

const roomOptions = [
  { value: "1+0", label: "1+0" },
  { value: "1+1", label: "1+1" },
  { value: "2+1", label: "2+1" },
  { value: "3+1", label: "3+1" },
  { value: "4+1", label: "4+1" },
  { value: "5+", label: "5+" },
]

const genderOptions = [
  { value: "erkek", label: "Erkek" },
  { value: "kadin", label: "Kadın" },
  { value: "belirtilmemis", label: "Belirtilmemiş" },
]

const ageRangeOptions = [
  { value: "18-25", label: "18-25" },
  { value: "26-35", label: "26-35" },
  { value: "36-45", label: "36-45" },
  { value: "46-55", label: "46-55" },
  { value: "56-65", label: "56-65" },
  { value: "65+", label: "65+" },
]

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export interface CustomerFormProps {
  defaultValues?: Partial<CustomerFormValues>
  isEditing?: boolean
  onSubmit: (data: CustomerFormValues) => void
  isLoading?: boolean
  className?: string
}

export function CustomerForm({
  defaultValues,
  isEditing = false,
  onSubmit,
  isLoading = false,
  className,
}: CustomerFormProps) {
  const form = useForm<CustomerFormValues>({
    resolver: zodResolver(customerFormSchema),
    defaultValues: {
      full_name: "",
      phone: "",
      email: "",
      customer_type: "buyer",
      source: "manual",
      budget_min: undefined,
      budget_max: undefined,
      desired_rooms: "",
      desired_area_min: undefined,
      desired_area_max: undefined,
      desired_districts: [],
      tags: [],
      notes: "",
      gender: "",
      age_range: "",
      profession: "",
      family_size: undefined,
      ...defaultValues,
    },
  })

  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = form

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className={cn("space-y-6", className)}
    >
      {/* Bölüm 1: Temel Bilgiler */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
        <FormSection title="Temel Bilgiler">
          <Input
            label="Ad Soyad *"
            placeholder="Örn: Ahmet Yılmaz"
            errorMessage={errors.full_name?.message}
            {...register("full_name")}
          />

          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Telefon"
              placeholder="0555 555 55 55"
              errorMessage={errors.phone?.message}
              {...register("phone")}
            />
            <Input
              label="E-posta"
              type="email"
              placeholder="ornek@email.com"
              errorMessage={errors.email?.message}
              {...register("email")}
            />
          </div>

          <Controller
            name="source"
            control={control}
            render={({ field }) => (
              <Select
                label="Müşteri Kaynağı"
                options={sources}
                placeholder="Kaynak seçin"
                errorMessage={errors.source?.message}
                {...field}
              />
            )}
          />
        </FormSection>
      </div>

      {/* Bölüm 2: Demografik Bilgiler */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
        <FormSection title="Demografik Bilgiler">
          <div className="grid gap-4 sm:grid-cols-2">
            <Controller
              name="gender"
              control={control}
              render={({ field }) => (
                <Select
                  label="Cinsiyet"
                  options={genderOptions}
                  placeholder="Seçiniz"
                  errorMessage={errors.gender?.message}
                  {...field}
                />
              )}
            />
            <Controller
              name="age_range"
              control={control}
              render={({ field }) => (
                <Select
                  label="Yaş Aralığı"
                  options={ageRangeOptions}
                  placeholder="Seçiniz"
                  errorMessage={errors.age_range?.message}
                  {...field}
                />
              )}
            />
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <Input
              label="Meslek"
              placeholder="Örn: Mühendis, Avukat, Öğretmen"
              errorMessage={errors.profession?.message}
              {...register("profession")}
            />
            <Controller
              name="family_size"
              control={control}
              render={({ field }) => (
                <NumberInput
                  label="Aile Büyüklüğü"
                  placeholder="Kişi sayısı"
                  min={1}
                  max={10}
                  value={field.value}
                  onChange={field.onChange}
                  errorMessage={errors.family_size?.message}
                />
              )}
            />
          </div>
        </FormSection>
      </div>

      {/* Bölüm 3: Müşteri Tipi (eski Bölüm 2) */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
        <FormSection title="Müşteri Tipi">
          <Controller
            name="customer_type"
            control={control}
            render={({ field }) => (
              <SegmentedControl
                options={customerTypes}
                value={field.value}
                onChange={field.onChange}
                error={errors.customer_type?.message}
              />
            )}
          />
        </FormSection>
      </div>

      {/* Bölüm 3: Bütçe */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
        <FormSection title="Bütçe">
          <div className="grid gap-4 sm:grid-cols-2">
            <Controller
              name="budget_min"
              control={control}
              render={({ field }) => (
                <NumberInput
                  label="Min Bütçe"
                  suffix="₺"
                  placeholder="Min"
                  value={field.value}
                  onChange={field.onChange}
                  errorMessage={errors.budget_min?.message}
                />
              )}
            />
            <Controller
              name="budget_max"
              control={control}
              render={({ field }) => (
                <NumberInput
                  label="Max Bütçe"
                  suffix="₺"
                  placeholder="Max"
                  value={field.value}
                  onChange={field.onChange}
                  errorMessage={errors.budget_max?.message}
                />
              )}
            />
          </div>
        </FormSection>
      </div>

      {/* Bölüm 4: Tercihler */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
        <FormSection title="Tercihler">
          <Controller
            name="desired_rooms"
            control={control}
            render={({ field }) => (
              <Select
                label="Oda Sayısı"
                options={roomOptions}
                placeholder="Seçiniz"
                errorMessage={errors.desired_rooms?.message}
                {...field}
              />
            )}
          />

          <div className="grid gap-4 sm:grid-cols-2">
            <Controller
              name="desired_area_min"
              control={control}
              render={({ field }) => (
                <NumberInput
                  label="Min m²"
                  suffix="m²"
                  placeholder="Min"
                  value={field.value}
                  onChange={field.onChange}
                  errorMessage={errors.desired_area_min?.message}
                />
              )}
            />
            <Controller
              name="desired_area_max"
              control={control}
              render={({ field }) => (
                <NumberInput
                  label="Max m²"
                  suffix="m²"
                  placeholder="Max"
                  value={field.value}
                  onChange={field.onChange}
                  errorMessage={errors.desired_area_max?.message}
                />
              )}
            />
          </div>

          <Controller
            name="desired_districts"
            control={control}
            render={({ field }) => (
              <TagInput
                label="Tercih Edilen İlçeler"
                placeholder="İlçe yazıp Enter'a basın"
                value={field.value}
                onChange={field.onChange}
                error={errors.desired_districts?.message}
              />
            )}
          />
        </FormSection>
      </div>

      {/* Bölüm 5: Etiketler */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
        <FormSection title="Etiketler">
          <Controller
            name="tags"
            control={control}
            render={({ field }) => (
              <TagInput
                placeholder="Etiket yazıp Enter'a basın"
                value={field.value}
                onChange={field.onChange}
                error={errors.tags?.message}
              />
            )}
          />
        </FormSection>
      </div>

      {/* Bölüm 6: Notlar */}
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6">
        <FormSection title="Notlar">
           <div className="space-y-2">
            <label className="text-sm font-medium leading-none text-gray-900">
              Notlar
            </label>
            <textarea
              placeholder="Müşteri hakkında notlar..."
              rows={4}
              className={cn(
                "flex w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y",
                errors.notes &&
                  "border-red-500 focus-visible:ring-red-500"
              )}
              {...register("notes")}
            />
            {errors.notes && (
              <p className="text-sm text-red-500">
                {errors.notes.message}
              </p>
            )}
          </div>
        </FormSection>
      </div>

      <Button type="submit" size="lg" fullWidth loading={isLoading}>
        {isLoading
          ? "Kaydediliyor..."
          : isEditing
            ? "Müşteriyi Güncelle"
            : "Müşteri Oluştur"}
      </Button>
    </form>
  )
}
