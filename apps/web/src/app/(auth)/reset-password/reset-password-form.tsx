"use client";

import { useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api-client";

export function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  // Token yoksa hata göster
  if (!token) {
    return (
      <div className="rounded-lg bg-red-50 p-4 text-center">
        <h3 className="text-sm font-semibold text-red-800">
          Geçersiz sıfırlama linki
        </h3>
        <p className="mt-2 text-sm text-red-700">
          Şifre sıfırlama linki geçersiz veya eksik. Lütfen yeni bir sıfırlama
          talebi oluşturun.
        </p>
        <Link
          href="/forgot-password"
          className="mt-4 inline-block text-sm font-semibold text-blue-600 hover:text-blue-500"
        >
          Yeni sıfırlama talebi
        </Link>
      </div>
    );
  }

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setValidationError(null);
    setIsLoading(true);

    const formData = new FormData(e.currentTarget);
    const newPassword = formData.get("new_password") as string;
    const confirmPassword = formData.get("confirm_password") as string;

    // Client-side validasyon
    if (newPassword !== confirmPassword) {
      setValidationError("Şifreler eşleşmiyor.");
      setIsLoading(false);
      return;
    }

    if (newPassword.length < 8) {
      setValidationError("Şifre en az 8 karakter olmalıdır.");
      setIsLoading(false);
      return;
    }

    try {
      await api.post("/auth/reset-password", {
        token,
        new_password: newPassword,
      });
      setIsSuccess(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(
          err.detail || "Bir hata oluştu. Lütfen tekrar deneyin."
        );
      } else {
        setError("Beklenmeyen bir hata oluştu.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className="rounded-lg bg-green-50 p-4 text-center">
        <div className="mb-2 text-2xl">&#10003;</div>
        <h3 className="text-sm font-semibold text-green-800">
          Şifreniz güncellendi!
        </h3>
        <p className="mt-2 text-sm text-green-700">
          Şifreniz başarıyla değiştirildi. Yeni şifrenizle giriş
          yapabilirsiniz.
        </p>
        <Link
          href="/login"
          className="mt-4 inline-block rounded-md bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-500"
        >
          Giriş Yap
        </Link>
      </div>
    );
  }

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
      {error && (
        <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">
          {error}
        </div>
      )}
      {validationError && (
        <div className="rounded-md bg-yellow-50 p-3 text-sm text-yellow-700">
          {validationError}
        </div>
      )}

      <div>
        <Input
          id="new_password"
          name="new_password"
          type="password"
          autoComplete="new-password"
          required
          label="Yeni şifre"
          placeholder="En az 8 karakter"
        />
      </div>

      <div>
        <Input
          id="confirm_password"
          name="confirm_password"
          type="password"
          autoComplete="new-password"
          required
          label="Yeni şifre (tekrar)"
          placeholder="Şifrenizi tekrar girin"
        />
      </div>

      <div>
        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? "Güncelleniyor..." : "Şifremi Güncelle"}
        </Button>
      </div>
    </form>
  );
}
