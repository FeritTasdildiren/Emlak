"use client";

import { use } from "react";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/button";
import { PropertyForm } from "@/components/properties/property-form";
import { PropertyFormValues } from "@/components/properties/property-form-schema";
import { usePropertyDetail } from "@/hooks/use-property-detail";
import { useUpdateProperty } from "@/hooks/use-properties";
import { Skeleton } from "@/components/ui/skeleton";
import { useRouter } from "next/navigation";
import { toast } from "@/components/ui/toast";

export default function EditPropertyPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { property, isLoading, isError } = usePropertyDetail(id);
  const { mutate: updateProperty } = useUpdateProperty();

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-4">
          <Skeleton className="h-9 w-9 rounded-lg" />
          <div className="space-y-2">
            <Skeleton className="h-7 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <div className="space-y-6">
          <Skeleton className="h-[400px] w-full rounded-xl" />
          <Skeleton className="h-[200px] w-full rounded-xl" />
        </div>
      </div>
    );
  }

  if (isError || !property) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-center">
        <h2 className="text-xl font-bold text-gray-900">Mülk bulunamadı</h2>
        <p className="text-gray-500 mt-2">
          Düzenlemek istediğiniz mülk mevcut değil veya yetkiniz yok.
        </p>
        <Button
          variant="outline"
          className="mt-6"
          onClick={() => router.push("/properties")}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Listeye Dön
        </Button>
      </div>
    );
  }

  const handleSubmit = (data: PropertyFormValues) => {
    updateProperty(
      { id, data: data as unknown as Record<string, unknown> },
      {
        onSuccess: () => {
          toast("İlan başarıyla güncellendi!");
          router.push(`/properties/${id}`);
        },
        onError: (error: Error) => {
          toast(error?.message || "Güncelleme sırasında bir hata oluştu");
        },
      }
    );
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href={`/properties/${id}`}>
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">İlanı Düzenle</h1>
          <p className="mt-1 text-sm text-gray-500">
            {property.title}
          </p>
        </div>
      </div>

      {/* Form */}
      <PropertyForm
        isEditing
        defaultValues={property as unknown as PropertyFormValues}
        className="max-w-3xl"
        onSubmit={handleSubmit}
      />
    </div>
  );
}
