"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "@/components/ui/toast";
import { api, ApiError } from "@/lib/api-client";

/* Demo ofis UUID — sunucuda mevcut PetQas Demo Ofis */
const DEMO_OFFICE_ID = "a1b2c3d4-e5f6-7890-abcd-ef1234567890";

export function RegisterForm() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);

    const formData = new FormData(e.currentTarget);
    const name = (formData.get("name") as string).trim();
    const surname = (formData.get("surname") as string).trim();
    const email = formData.get("email") as string;
    const password = formData.get("password") as string;

    if (password.length < 8) {
      toast("Şifre en az 8 karakter olmalıdır.", "error");
      setLoading(false);
      return;
    }

    try {
      await api.post("/auth/register", {
        email,
        password,
        full_name: `${name} ${surname}`,
        office_id: DEMO_OFFICE_ID,
      });

      toast("Kayıt başarılı! Giriş sayfasına yönlendiriliyorsunuz...", "success");
      router.push("/login");
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 409 || error.detail?.includes("zaten")) {
          toast("Bu e-posta adresi zaten kayıtlı. Giriş yapmayı deneyin.", "error");
        } else if (error.status === 429) {
          toast("Çok fazla deneme yaptınız. Lütfen biraz bekleyin.", "error");
        } else {
          toast(error.detail || "Kayıt başarısız. Lütfen tekrar deneyin.", "error");
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
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Input
          id="name"
          name="name"
          type="text"
          autoComplete="given-name"
          required
          label="Ad"
          placeholder="Adınız"
        />
        <Input
          id="surname"
          name="surname"
          type="text"
          autoComplete="family-name"
          required
          label="Soyad"
          placeholder="Soyadınız"
        />
      </div>

      <Input
        id="email"
        name="email"
        type="email"
        autoComplete="email"
        required
        label="E-posta adresi"
        placeholder="ornek@sirket.com"
      />

      <Input
        id="office"
        name="office"
        type="text"
        required
        label="Ofis / Şirket Adı"
        placeholder="Örn: Emlak Ofisi A.Ş."
      />

      <Input
        id="password"
        name="password"
        type="password"
        autoComplete="new-password"
        required
        label="Şifre"
        minLength={8}
      />

      <div>
        <Button type="submit" className="w-full" disabled={loading}>
          {loading ? "Kayıt oluşturuluyor..." : "Kayıt Ol"}
        </Button>
      </div>
    </form>
  );
}
