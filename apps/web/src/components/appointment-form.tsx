"use client";

import * as React from "react";
import { useForm, Controller } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Appointment } from "@/types/appointment";

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
  customer_id: z.string().uuid("Geçerli bir müşteri ID'si giriniz").optional().or(z.literal("")),
  property_id: z.string().uuid("Geçerli bir ilan ID'si giriniz").optional().or(z.literal("")),
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
              "flex w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y",
              errors.description && "border-red-500 focus-visible:ring-red-500"
            )}
            {...register("description")}
          />
          {errors.description && (
            <p className="text-sm text-red-500">{errors.description.message}</p>
          )}
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <Input
            label="Müşteri ID (Opsiyonel)"
            placeholder="UUID formatında"
            errorMessage={errors.customer_id?.message}
            {...register("customer_id")}
          />
          <Input
            label="İlan ID (Opsiyonel)"
            placeholder="UUID formatında"
            errorMessage={errors.property_id?.message}
            {...register("property_id")}
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
              "flex w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50 resize-y",
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
