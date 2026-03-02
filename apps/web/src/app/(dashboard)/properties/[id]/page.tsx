"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import { usePropertyDetail } from "@/hooks/use-property-detail";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  ChevronLeft,
  Edit,
  MapPin,
  Ruler,
  Home,
  Building2,
  LandPlot,
  Calendar,
  Layers,
  Flame,
  User,
  Info,
} from "lucide-react";
import { formatCurrency, formatDate } from "@/lib/utils";
import {
  heatingTypeOptions,
} from "@/components/properties/property-form-schema";

const statusConfig: Record<
  string,
  { label: string; variant: "success" | "default" | "warning" | "secondary" }
> = {
  active: { label: "Aktif", variant: "success" },
  sold: { label: "Satıldı", variant: "default" },
  rented: { label: "Kiralandı", variant: "warning" },
  draft: { label: "Taslak", variant: "secondary" },
};

const typeConfig: Record<
  string,
  { label: string; icon: typeof Home }
> = {
  daire: { label: "Daire", icon: Home },
  villa: { label: "Villa", icon: Home },
  ofis: { label: "Ofis", icon: Building2 },
  arsa: { label: "Arsa", icon: LandPlot },
  dukkan: { label: "Dükkan", icon: Building2 },
};

export default function PropertyDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const { property, isLoading, isError } = usePropertyDetail(id);

  if (isLoading) {
    return <PropertyDetailSkeleton />;
  }

  if (isError || !property) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <h2 className="text-2xl font-bold text-gray-900">Mülk bulunamadı</h2>
        <p className="text-gray-500 mt-2">
          Aradığınız mülk silinmiş olabilir veya erişim yetkiniz yok.
        </p>
        <Button
          variant="outline"
          className="mt-6"
          onClick={() => router.push("/properties")}
        >
          <ChevronLeft className="mr-2 h-4 w-4" />
          Listeye Dön
        </Button>
      </div>
    );
  }

  const status = statusConfig[property.status] || statusConfig.draft;
  const type = typeConfig[property.property_type] || typeConfig.daire;
  const TypeIcon = type.icon;
  const heatingLabel = heatingTypeOptions.find(
    (h) => h.value === property.heating_type
  )?.label;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => router.push("/properties")}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <h1 className="text-2xl font-bold text-gray-900 truncate max-w-[400px]">
            {property.title}
          </h1>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            onClick={() => router.push(`/properties/edit/${property.id}`)}
          >
            <Edit className="mr-2 h-4 w-4" />
            Düzenle
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Photo Placeholder */}
          <Card className="aspect-video relative overflow-hidden flex flex-col items-center justify-center bg-gray-50 border-2 border-dashed">
            <Info className="h-12 w-12 text-gray-300 mb-2" />
            <p className="text-gray-400 font-medium">Henüz fotoğraf eklenmemiş</p>
          </Card>

          {/* Description */}
          <Card className="p-6">
            <h3 className="text-lg font-bold mb-4">Açıklama</h3>
            <div className="prose prose-sm max-w-none text-gray-600">
              {property.description ? (
                <p className="whitespace-pre-wrap">{property.description}</p>
              ) : (
                <p className="italic text-gray-400">Açıklama belirtilmemiş.</p>
              )}
            </div>
          </Card>

          {/* Features */}
          <Card className="p-6">
            <h3 className="text-lg font-bold mb-4">Mülk Özellikleri</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-y-6 gap-x-4">
              <FeatureItem
                icon={TypeIcon}
                label="Mülk Tipi"
                value={type.label}
              />
              <FeatureItem
                icon={Layers}
                label="Oda Sayısı"
                value={property.room_count || "Belirtilmemiş"}
              />
              <FeatureItem
                icon={Ruler}
                label="Alan"
                value={`${property.area_sqm} m²`}
              />
              <FeatureItem
                icon={Layers}
                label="Bulunduğu Kat"
                value={property.floor != null ? `${property.floor}. Kat` : "Belirtilmemiş"}
              />
              <FeatureItem
                icon={Building2}
                label="Bina Yaşı"
                value={property.building_age != null ? `${property.building_age} Yıl` : "Belirtilmemiş"}
              />
              <FeatureItem
                icon={Flame}
                label="Isınma"
                value={heatingLabel || "Belirtilmemiş"}
              />
            </div>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          <Card className="p-6">
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-500">Fiyat</p>
                <div className="flex items-baseline gap-2">
                  <h2 className="text-3xl font-bold text-gray-900">
                    {formatCurrency(property.price)}
                  </h2>
                  {property.listing_type === "kiralik" && (
                    <span className="text-gray-500">/ay</span>
                  )}
                </div>
              </div>
              <Badge variant={status.variant} className="w-full justify-center py-1 text-sm">
                {status.label}
              </Badge>
              <div className="pt-4 border-t space-y-3">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <MapPin className="h-4 w-4 text-gray-400" />
                  <span>
                    {property.district}, {property.city}
                  </span>
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Calendar className="h-4 w-4 text-gray-400" />
                  <span>Eklenme: {formatDate(property.created_at)}</span>
                </div>
              </div>
            </div>
          </Card>

          <Card className="p-6">
            <h4 className="font-bold mb-4">Hızlı Aksiyonlar</h4>
            <div className="space-y-2">
              <Button variant="outline" className="w-full justify-start" disabled>
                <User className="mr-2 h-4 w-4" />
                Müşteri Eşleştir (Yakında)
              </Button>
              <Button variant="outline" className="w-full justify-start" disabled>
                <Calendar className="mr-2 h-4 w-4" />
                Randevu Oluştur (Yakında)
              </Button>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

function FeatureItem({
  icon: Icon,
  label,
  value,
}: {
  icon: React.ElementType;
  label: string;
  value: string | number;
}) {
  return (
    <div className="flex items-start gap-3">
      <div className="p-2 bg-gray-50 rounded-lg text-gray-500 shrink-0">
        <Icon className="h-4 w-4" />
      </div>
      <div>
        <p className="text-xs text-gray-500 uppercase tracking-wider font-semibold">
          {label}
        </p>
        <p className="text-sm font-medium text-gray-900">{value}</p>
      </div>
    </div>
  );
}

function PropertyDetailSkeleton() {
  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Skeleton className="h-9 w-9" />
          <Skeleton className="h-8 w-64" />
        </div>
        <Skeleton className="h-10 w-32" />
      </div>
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <Skeleton className="aspect-video w-full" />
          <Card className="p-6 space-y-4">
            <Skeleton className="h-6 w-32" />
            <Skeleton className="h-20 w-full" />
          </Card>
          <Card className="p-6 space-y-4">
            <Skeleton className="h-6 w-32" />
            <div className="grid grid-cols-3 gap-6">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="flex gap-3">
                  <Skeleton className="h-8 w-8" />
                  <div className="space-y-2">
                    <Skeleton className="h-3 w-16" />
                    <Skeleton className="h-4 w-24" />
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
        <div className="space-y-6">
          <Card className="p-6 space-y-6">
            <div className="space-y-2">
              <Skeleton className="h-4 w-12" />
              <Skeleton className="h-10 w-32" />
            </div>
            <Skeleton className="h-8 w-full rounded-full" />
            <div className="space-y-2 pt-4">
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-2/3" />
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
