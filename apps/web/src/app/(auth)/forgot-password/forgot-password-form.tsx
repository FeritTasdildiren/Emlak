"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api-client";

export function ForgotPasswordForm() {
  const [isLoading, setIsLoading] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    const formData = new FormData(e.currentTarget);
    const email = formData.get("email") as string;

    try {
      await api.post("/auth/forgot-password", { email });
      setIsSubmitted(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail || "Bir hata oluştu. Lütfen tekrar deneyin.");
      } else {
        setError("Beklenmeyen bir hata oluştu.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  if (isSubmitted) {
    return (
      <div className="rounded-lg bg-green-50 p-4 text-center">
        <div className="mb-2 text-2xl">&#9993;</div>
        <h3 className="text-sm font-semibold text-green-800">
          E-posta gönderildi!
        </h3>
        <p className="mt-2 text-sm text-green-700">
          Eğer bu e-posta adresiyle bir hesap varsa, şifre sıfırlama linki
          gönderildi. Lütfen gelen kutunuzu kontrol edin.
        </p>
        <p className="mt-4 text-xs text-green-600">
          E-postayı alamadınız mı? Spam klasörünüzü kontrol edin veya birkaç
          dakika bekleyip tekrar deneyin.
        </p>
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

      <div>
        <Input
          id="email"
          name="email"
          type="email"
          autoComplete="email"
          required
          label="E-posta adresi"
          placeholder="ornek@sirket.com"
        />
      </div>

      <div>
        <Button type="submit" className="w-full" disabled={isLoading}>
          {isLoading ? "Gönderiliyor..." : "Sıfırlama Linki Gönder"}
        </Button>
      </div>
    </form>
  );
}
