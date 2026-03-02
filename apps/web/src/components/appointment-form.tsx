"use client";

import * as React from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { SearchableSelect } from "@/components/ui/searchable-select";
import { Appointment } from "@/types/appointment";
import { useCustomerSearch } from "@/hooks/use-customer-search";
import { usePropertySearch } from "@/hooks/use-property-search";
import { useCustomerDetail } from "@/hooks/use-customers";
import { usePropertyDetail } from "@/hooks/use-property-detail";

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const appointmentFormSchema = z.object({
  title: z.string().min(3, "Başlık en az 3 karakter olmalıdır"),
  description: z.string().optional(),
  appointment_date: z.string().min(1, "Randevu tarihi zorunludur"),
  duration_minutes: z.string().min(1, "Süre seçiniz"),
  status: z.enum(["scheduled", "completed", "cancelled", "no_show"]),
  location: z.string().optional(),
  notes: z.string().optional(),
  customer_id: z.string().optional().or(z.literal("")),
  property_id: z.string().optional().or(z.literal("")),
});

export type AppointmentFormValues = z.infer<typeof appointmentFormSchema>;

// ---------------------------------------------------------------------------
// Data
// ---------------------------------------------------------------------------

const durationOptions = [
  { value: "15", label: "15 Dakika" },
  { value: "30", label: "30 Dakika" },
  { value: "45", label: "45 Dakika" },
  { value: "60", label: "1 Saat" },
  { value: "90", label: "1.5 Saat" },
  { value: "120", label: "2 Saat" },
];

const statusOptions = [
  { value: "scheduled", label: "Planlandı" },
  { value: "completed", label: "Tamamlandı" },
  { value: "cancelled", label: "İptal Edildi" },
  { value: "no_show", label: "Gelmedi" },
];

const customerTypeLabelMap: Record<string, string> = {
  buyer: "Alıcı",
  seller: "Satıcı",
  renter: "Kiracı",
  landlord: "Ev Sahibi",
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export interface AppointmentFormProps {
  defaultValues?: Appointment;
  isEditing?: boolean;
  onSubmit: (data: AppointmentFormValues) => void;
  isLoading?: boolean;
  className?: string;
}

export function AppointmentForm({
  defaultValues,
  isEditing = false,
  onSubmit,
  isLoading = false,
  className,
}: AppointmentFormProps) {
  // datetime-local için tarihi formatla (YYYY-MM-DDThh:mm)
  const formatForInput = (dateString?: string) => {
    if (!dateString) return "";
    const date = new Date(dateString);
    const tzoffset = date.getTimezoneOffset() * 60000; //ms
    const localISOTime = new Date(date.getTime() - tzoffset).toISOString().slice(0, 16);
    return localISOTime;
  };

  const form = useForm<AppointmentFormValues>({
    resolver: zodResolver(appointmentFormSchema),
    defaultValues: {
      title: defaultValues?.title || "",
      description: defaultValues?.description || "",
      appointment_date: defaultValues?.appointment_date 
        ? formatForInput(defaultValues.appointment_date) 
        : formatForInput(new Date().toISOString()),
      duration_minutes: defaultValues?.duration_minutes?.toString() || "30",
      status: (defaultValues?.status as Appointment["status"]) || "scheduled",
      location: defaultValues?.location || "",
      notes: defaultValues?.notes || "",
      customer_id: defaultValues?.customer_id || "",
      property_id: defaultValues?.property_id || "",
    },
  });

  const {
    register,
    handleSubmit,
    control,
    formState: { errors },
  } = form;

  const [customerQuery, setCustomerQuery] = React.useState("");
  const [propertyQuery, setPropertyQuery] = React.useState("");

  const { data: customerOptions = [], isLoading: isCustomerLoading } = useCustomerSearch(customerQuery);
  const { data: propertyOptions = [], isLoading: isPropertyLoading } = usePropertySearch(propertyQuery);

  // Mevcut müşteri/ilan bilgisini çekmek için detay hook'ları (düzenleme modunda etiket göstermek için)
  const watchedCustomerId = form.watch("customer_id");
  const watchedPropertyId = form.watch("property_id");

  const { data: customerDetail } = useCustomerDetail(watchedCustomerId || null);
  const { property: propertyDetail } = usePropertyDetail(watchedPropertyId || "");

  // Detay bilgisini arama sonuçlarıyla birleştir (seçili değerin etiketi görünsün)
  const mergedCustomerOptions = React.useMemo(() => {
    const opts = [...customerOptions];
    if (customerDetail && !opts.find(o => o.value === customerDetail.id)) {
      opts.unshift({
        value: customerDetail.id,
        label: `${customerDetail.full_name} (${customerTypeLabelMap[customerDetail.customer_type] || customerDetail.customer_type})`,
        sublabel: customerDetail.phone || "Telefon yok",
      });
    }
    return opts;
  }, [customerOptions, customerDetail]);

  const mergedPropertyOptions = React.useMemo(() => {
    const opts = [...propertyOptions];
    if (propertyDetail && !opts.find(o => o.value === propertyDetail.id)) {
      opts.unshift({
        value: propertyDetail.id,
        label: propertyDetail.title,
        sublabel: `${propertyDetail.city} ${propertyDetail.district} — ${propertyDetail.room_count || "?"} oda ${propertyDetail.area_sqm ?? 0} m²`,
      });
    }
    return opts;
  }, [propertyOptions, propertyDetail]);

  return (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className={cn("space-y-6", className)}
    >
      <div className="space-y-4">
        <Input
          label="Başlık *"
          placeholder="Örn: Portföy Sunumu"
          errorMessage={errors.title?.message}
          {...register("title")}
        />

        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Randevu Tarihi *"
            type="datetime-local"
            errorMessage={errors.appointment_date?.message}
            {...register("appointment_date")}
          />
          <Controller
            name="duration_minutes"
            control={control}
            render={({ field }) => (
              <Select
                label="Süre"
                options={durationOptions}
                placeholder="Süre seçin"
                errorMessage={errors.duration_minutes?.message}
                {...field}
              />
            )}
          />
        </div>

        <Controller
          name="status"
          control={control}
          render={({ field }) => (
            <Select
              label="Durum"
              options={statusOptions}
              placeholder="Durum seçin"
              errorMessage={errors.status?.message}
              {...field}
            />
          )}
        />

        <Input
          label="Konum"
          placeholder="Örn: Ofis veya İlan Adresi"
          errorMessage={errors.location?.message}
          {...register("location")}
        />

        <div className="space-y-2">
          <label className="text-sm font-medium leading-none text-gray-900">
            Açıklama
          </label>
          <textarea
            placeholder="Randevu hakkında kısa bilgi..."
            rows={3}
            className={cn(
              "flex w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-2 text-sm ring-offset-white dark:ring-offset-zinc-950 placeholder:text-zinc-500 dark:placeholder:text-zinc-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y",
              errors.description && "border-red-500 focus-visible:ring-red-500"
            )}
            {...register("description")}
          />
          {errors.description && (
            <p className="text-sm text-red-500">{errors.description.message}</p>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Controller
            name="customer_id"
            control={control}
            render={({ field }) => (
              <SearchableSelect
                label="Müşteri"
                placeholder="Müşteri ara..."
                options={mergedCustomerOptions}
                onSearch={setCustomerQuery}
                isLoading={isCustomerLoading}
                errorMessage={errors.customer_id?.message}
                {...field}
              />
            )}
          />
          <Controller
            name="property_id"
            control={control}
            render={({ field }) => (
              <SearchableSelect
                label="İlan"
                placeholder="İlan ara..."
                options={mergedPropertyOptions}
                onSearch={setPropertyQuery}
                isLoading={isPropertyLoading}
                errorMessage={errors.property_id?.message}
                {...field}
              />
            )}
          />
        </div>

        <div className="space-y-2">
          <label className="text-sm font-medium leading-none text-gray-900">
            Notlar (Dahili)
          </label>
          <textarea
            placeholder="Sadece sizin göreceğiniz notlar..."
            rows={3}
            className={cn(
              "flex w-full rounded-lg border border-zinc-300 dark:border-zinc-700 bg-white dark:bg-zinc-950 px-3 py-2 text-sm ring-offset-white dark:ring-offset-zinc-950 placeholder:text-zinc-500 dark:placeholder:text-zinc-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y",
              errors.notes && "border-red-500 focus-visible:ring-red-500"
            )}
            {...register("notes")}
          />
          {errors.notes && (
            <p className="text-sm text-red-500">{errors.notes.message}</p>
          )}
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t">
        <Button type="submit" loading={isLoading}>
          {isEditing ? "Randevuyu Güncelle" : "Randevu Oluştur"}
        </Button>
      </div>
    </form>
  );
}
