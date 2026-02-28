"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, UserPlus } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { toast } from "@/components/ui/toast";

const customerTypes = [
  { value: "buyer", label: "Alıcı" },
  { value: "seller", label: "Satıcı" },
  { value: "renter", label: "Kiracı" },
  { value: "landlord", label: "Ev Sahibi" },
];

const leadStatuses = [
  { value: "cold", label: "Soğuk" },
  { value: "warm", label: "Ilık" },
  { value: "hot", label: "Sıcak" },
];

export default function NewCustomerPage() {
  const router = useRouter();

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    // Demo modda — API henüz yok
    toast("Müşteri başarıyla oluşturuldu! (Demo)", "success");
    router.push("/dashboard/customers");
  };

  return (
    <div className="px-4 sm:px-6 lg:px-8 py-8 w-full max-w-2xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/dashboard/customers">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Yeni Müşteri</h1>
          <p className="mt-1 text-sm text-gray-500">
            Portföyünüze yeni bir müşteri ekleyin.
          </p>
        </div>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Kişisel Bilgiler</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Ad"
              name="first_name"
              placeholder="Adı"
              required
            />
            <Input
              label="Soyad"
              name="last_name"
              placeholder="Soyadı"
              required
            />
          </div>

          <Input
            label="E-posta"
            name="email"
            type="email"
            placeholder="ornek@mail.com"
          />

          <Input
            label="Telefon"
            name="phone"
            type="tel"
            placeholder="05XX XXX XX XX"
            required
          />
        </div>

        <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-sm sm:p-6 space-y-4">
          <h2 className="text-lg font-semibold text-gray-900">Müşteri Detayları</h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Select
              label="Müşteri Tipi"
              name="customer_type"
              options={customerTypes}
              placeholder="Tip seçin"
            />
            <Select
              label="İlgi Durumu"
              name="lead_status"
              options={leadStatuses}
              placeholder="Durum seçin"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-medium leading-none text-gray-900">
              Not
            </label>
            <textarea
              name="notes"
              rows={3}
              placeholder="Müşteri hakkında notlar (opsiyonel)"
              className="flex w-full rounded-lg border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 resize-none"
            />
          </div>
        </div>

        <Button type="submit" size="lg" className="w-full">
          <UserPlus className="mr-2 h-4 w-4" />
          Müşteri Oluştur
        </Button>
      </form>
    </div>
  );
}
