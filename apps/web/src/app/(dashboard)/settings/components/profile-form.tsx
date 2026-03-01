"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Avatar } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { FormField } from "@/components/ui/form-field";
import { toast } from "@/components/ui/toast";
import { useProfile } from "@/hooks/use-profile";
import { api, ApiError } from "@/lib/api-client";
import type { ProfileFormValues } from "@/types/settings";

// ================================================================
// Zod validasyon şeması
// ================================================================

const profileSchema = z.object({
  full_name: z
    .string()
    .min(2, "Ad soyad en az 2 karakter olmalıdır")
    .max(100, "Ad soyad en fazla 100 karakter olabilir"),
  phone: z
    .string()
    .regex(/^(\+90|0)?[0-9]{10}$/, "Geçerli bir telefon numarası girin")
    .or(z.literal("")),
});

// ================================================================
// Profil Formu Bileşeni
// ================================================================

export function ProfileForm() {
  const { user, isLoading, isError, refetch } = useProfile();

  const {
    control,
    handleSubmit,
    reset,
    formState: { isSubmitting, isDirty },
  } = useForm<ProfileFormValues>({
    resolver: zodResolver(profileSchema),
    defaultValues: {
      full_name: "",
      phone: "",
    },
  });

  // Kullanıcı verisi geldiğinde formu doldur
  useEffect(() => {
    if (user) {
      reset({
        full_name: user.full_name || "",
        phone: user.phone || "",
      });
    }
  }, [user, reset]);

  const onSubmit = async (data: ProfileFormValues) => {
    try {
      await api.put("/auth/me", {
        full_name: data.full_name,
        phone: data.phone || null,
      });
      toast("Profil bilgileriniz başarıyla güncellendi.", "success");
      // Profil verisini yeniden çek — form ve sidebar güncellensin
      await refetch();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 401) {
          toast("Oturumunuz sona ermiş. Lütfen tekrar giriş yapın.", "error");
          return;
        }
        if (err.status === 422) {
          toast("Girdiğiniz bilgilerde hata var. Lütfen kontrol edin.", "error");
          return;
        }
        toast(err.detail || "Profil güncellenirken bir hata oluştu.", "error");
        return;
      }
      toast("Profil güncellenirken bir hata oluştu. Lütfen tekrar deneyin.", "error");
    }
  };

  // Yükleniyor durumu
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Profil Bilgileri</CardTitle>
          <CardDescription>Hesap bilgilerinizi görüntüleyin ve düzenleyin.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="flex items-center gap-4">
            <Skeleton className="h-16 w-16 rounded-full" />
            <div className="space-y-2">
              <Skeleton className="h-4 w-32" />
              <Skeleton className="h-3 w-24" />
            </div>
          </div>
          <div className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        </CardContent>
      </Card>
    );
  }

  // Hata durumu
  if (isError) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Profil Bilgileri</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
            Profil bilgileri yüklenirken bir hata oluştu. Lütfen sayfayı yenileyin.
          </div>
        </CardContent>
      </Card>
    );
  }

  const initials = user?.full_name
    ? user.full_name
        .split(" ")
        .map((n) => n[0])
        .join("")
        .slice(0, 2)
    : "??";

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Profil Bilgileri</CardTitle>
        <CardDescription>Hesap bilgilerinizi görüntüleyin ve düzenleyin.</CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          {/* Avatar bölümü */}
          <div className="flex items-center gap-4">
            <Avatar fallback={initials} className="h-16 w-16 text-lg" />
            <div>
              <p className="font-medium text-gray-900">{user?.full_name}</p>
              <p className="text-sm text-gray-500">{user?.email}</p>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                disabled
                className="mt-1 px-0 text-blue-600 hover:text-blue-700"
              >
                Fotoğraf değiştir (yakında)
              </Button>
            </div>
          </div>

          <div className="h-px bg-gray-200" />

          {/* Form alanları */}
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              name="full_name"
              control={control}
              label="Ad Soyad"
            >
              <Input placeholder="Ad Soyad" />
            </FormField>

            <FormField
              name="phone"
              control={control}
              label="Telefon"
              helperText="Örn: 05XX XXX XX XX"
            >
              <Input placeholder="05XX XXX XX XX" type="tel" />
            </FormField>
          </div>

          {/* E-posta (sadece okunur) */}
          <Input
            label="E-posta"
            value={user?.email || ""}
            disabled
            helperText="E-posta adresi değiştirilemez"
          />

          {/* Kaydet butonu */}
          <div className="flex justify-end">
            <Button
              type="submit"
              loading={isSubmitting}
              disabled={!isDirty}
            >
              Değişiklikleri Kaydet
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
