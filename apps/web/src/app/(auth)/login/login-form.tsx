"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "@/components/ui/toast";
import { api, ApiError } from "@/lib/api-client";
import { auth } from "@/lib/auth";

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export function LoginForm() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    const formData = new FormData(e.currentTarget);
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    try {
      const data = await api.post<TokenResponse>("/auth/login", {
        email,
        password,
      });

      auth.setToken(data.access_token);
      if (data.refresh_token) {
        localStorage.setItem("refresh_token", data.refresh_token);
      }

      toast("Giriş başarılı! Yönlendiriliyorsunuz...", "success");
      router.push("/valuations");
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 401) {
          toast("E-posta veya şifre hatalı.", "error");
        } else if (error.status === 429) {
          toast("Çok fazla deneme yaptınız. Lütfen biraz bekleyin.", "error");
        } else {
          toast(error.detail || "Giriş başarısız. Lütfen tekrar deneyin.", "error");
        }
      } else {
        toast("Bağlantı hatası. Lütfen internet bağlantınızı kontrol edin.", "error");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <form className="space-y-6" onSubmit={handleSubmit}>
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
        <div className="flex items-center justify-between mb-2">
          <label
            htmlFor="password"
            className="block text-sm font-medium leading-none text-gray-900"
          >
            Şifre
          </label>
          <div className="text-sm">
            <Link
              href="/forgot-password"
              className="font-semibold text-blue-600 hover:text-blue-500"
            >
              Şifremi unuttum?
            </Link>
          </div>
        </div>
        <div className="mt-2">
          <Input
            id="password"
            name="password"
            type="password"
            autoComplete="current-password"
            required
          />
        </div>
      </div>

      <div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Giriş yapılıyor..." : "Giriş Yap"}
        </Button>
      </div>
    </form>
  );
}
