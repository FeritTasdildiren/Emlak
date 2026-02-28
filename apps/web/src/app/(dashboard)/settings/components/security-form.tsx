"use client";

import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { FormField } from "@/components/ui/form-field";
import { toast } from "@/components/ui/toast";
import { useChangePassword } from "@/hooks/use-change-password";
import { ApiError } from "@/lib/api-client";
import type { ChangePasswordFormValues } from "@/types/settings";

// ================================================================
// Zod validasyon şeması
// ================================================================

const passwordSchema = z
  .object({
    current_password: z
      .string()
      .min(1, "Mevcut şifre gereklidir"),
    new_password: z
      .string()
      .min(8, "Yeni şifre en az 8 karakter olmalıdır")
      .regex(
        /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/,
        "Şifre en az bir büyük harf, bir küçük harf ve bir rakam içermelidir"
      ),
    new_password_confirm: z
      .string()
      .min(1, "Şifre tekrarı gereklidir"),
  })
  .refine((data) => data.new_password === data.new_password_confirm, {
    message: "Şifreler eşleşmiyor",
    path: ["new_password_confirm"],
  });

// ================================================================
// Güvenlik Formu Bileşeni
// ================================================================

export function SecurityForm() {
  const { changePasswordAsync, isPending } = useChangePassword();

  const {
    control,
    handleSubmit,
    reset,
    formState: { isValid },
  } = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: {
      current_password: "",
      new_password: "",
      new_password_confirm: "",
    },
    mode: "onChange",
  });

  const onSubmit = async (data: ChangePasswordFormValues) => {
    try {
      await changePasswordAsync({
        current_password: data.current_password,
        new_password: data.new_password,
      });
      toast("Şifreniz başarıyla değiştirildi", "success");
      reset();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.status === 400) {
          toast("Mevcut şifreniz hatalı", "error");
        } else if (err.status === 429) {
          toast("Çok fazla deneme yaptınız. Lütfen daha sonra tekrar deneyin.", "error");
        } else {
          toast(err.detail || "Şifre değiştirirken bir hata oluştu", "error");
        }
      } else {
        toast("Beklenmeyen bir hata oluştu", "error");
      }
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Şifre Değiştir</CardTitle>
        <CardDescription>
          Hesap güvenliğiniz için şifrenizi düzenli olarak değiştirin.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 max-w-md">
          <FormField
            name="current_password"
            control={control}
            label="Mevcut Şifre"
          >
            <Input type="password" placeholder="Mevcut şifrenizi girin" />
          </FormField>

          <FormField
            name="new_password"
            control={control}
            label="Yeni Şifre"
            helperText="En az 8 karakter, büyük harf, küçük harf ve rakam içermelidir"
          >
            <Input type="password" placeholder="Yeni şifrenizi girin" />
          </FormField>

          <FormField
            name="new_password_confirm"
            control={control}
            label="Yeni Şifre (Tekrar)"
          >
            <Input type="password" placeholder="Yeni şifrenizi tekrar girin" />
          </FormField>

          <div className="flex justify-end pt-2">
            <Button
              type="submit"
              loading={isPending}
              disabled={!isValid}
            >
              Şifreyi Değiştir
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
