"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { toast } from "@/components/ui/toast";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api-client";
import { PropertyCard } from "@/components/properties/property-card";
import type { Showcase } from "@/types/showcase";
import type { Property } from "@/types/property";
import { cn } from "@/lib/utils";
import { Check, Loader2 } from "lucide-react";

// ─── Backend Response Type ───────────────────────────────────────

interface ApiPropertyItem {
  id: string;
  title: string;
  description?: string | null;
  property_type: string;
  listing_type: string;
  price: number;
  currency: string;
  rooms: string | null;
  gross_area: number | null;
  net_area: number | null;
  floor_number: number | null;
  total_floors: number | null;
  building_age: number | null;
  city: string;
  district: string;
  neighborhood: string | null;
  status: string;
  photos: string[];
  created_at: string;
}

interface SearchApiResponse {
  items: ApiPropertyItem[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  query: string | null;
}

function mapApiToProperty(item: ApiPropertyItem): Property {
  return {
    id: item.id,
    title: item.title,
    property_type: item.property_type as Property["property_type"],
    listing_type: (item.listing_type === "sale" ? "satilik" : "kiralik") as Property["listing_type"],
    price: item.price,
    currency: item.currency,
    area_sqm: item.net_area ?? item.gross_area ?? 0,
    room_count: item.rooms ?? null,
    floor: item.floor_number,
    total_floors: item.total_floors,
    building_age: item.building_age,
    heating_type: null,
    bathroom_count: null,
    furniture_status: null,
    building_type: null,
    facade: null,
    city: item.city,
    district: item.district,
    neighborhood: item.neighborhood,
    address: null,
    status: item.status as Property["status"],
    created_at: item.created_at,
    updated_at: item.created_at,
  };
}

// ─── Component ───────────────────────────────────────────────────

interface ShowcaseFormProps {
  initialData?: Showcase;
}

const THEMES = [
  { id: "minimal", label: "Minimal", primary_color: "#1f2937", background: "light", layout: "grid" },
  { id: "modern", label: "Modern", primary_color: "#ea580c", background: "light", layout: "grid" },
  { id: "classic", label: "Klasik", primary_color: "#0f172a", background: "dark", layout: "list" },
];

export function ShowcaseForm({ initialData }: ShowcaseFormProps) {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [title, setTitle] = useState(initialData?.title || "");
  const [description, setDescription] = useState(initialData?.description || "");
  const [selectedProperties, setSelectedProperties] = useState<string[]>(
    initialData?.selected_properties || []
  );

  // Find matching theme or default to modern
  const defaultThemeId = initialData?.theme
    ? THEMES.find(t => t.primary_color === initialData.theme.primary_color && t.background === initialData.theme.background)?.id || "modern"
    : "modern";

  const [theme, setTheme] = useState(defaultThemeId);

  // ─── Ofis ilanlarını gerçek API'den çek ─────────────────────────
  const { data: properties = [], isLoading: isPropertiesLoading } = useQuery({
    queryKey: ["form-properties"],
    queryFn: async (): Promise<Property[]> => {
      const res = await api.get<SearchApiResponse>("/properties/search?limit=100&per_page=100");
      return res.items.map(mapApiToProperty);
    },
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });

  function toggleProperty(id: string) {
    setSelectedProperties((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : [...prev, id]
    );
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      const selectedTheme = THEMES.find((t) => t.id === theme) ?? THEMES[1];
      const payload = {
        title,
        description: description || undefined,
        selected_properties: selectedProperties,
        theme: selectedTheme.id,
      };

      if (initialData) {
        await api.put(`/showcases/${initialData.id}`, payload);
      } else {
        await api.post("/showcases", payload);
      }

      toast(`Vitrin başarıyla ${initialData ? "güncellendi" : "oluşturuldu"}!`);
      router.push("/network");
    } catch (error) {
      const message = error instanceof Error ? error.message : "Bir hata oluştu";
      toast(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-8">
      {/* Basic Info */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="space-y-2">
            <label htmlFor="title" className="text-sm font-medium text-gray-700">
              Vitrin Başlığı
            </label>
            <Input
              id="title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Örn: Seçkin Boğaz Manzaralı Yalılar"
              required
            />
          </div>
          <div className="space-y-2">
            <label htmlFor="description" className="text-sm font-medium text-gray-700">
              Vitrin Açıklaması
            </label>
            <Textarea
              id="description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Müşterilerinize vitrininiz hakkında kısa bir bilgi verin..."
              rows={3}
            />
          </div>
        </CardContent>
      </Card>

      {/* Property Selection */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium text-gray-900">İlan Seçimi</h3>
          <p className="text-sm text-gray-500">
            Vitrinde sergilemek istediğiniz ilanları seçin ({selectedProperties.length} seçildi)
          </p>
        </div>

        {isPropertiesLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <div
                key={i}
                className="h-40 rounded-lg bg-gray-100 animate-pulse"
              />
            ))}
          </div>
        ) : properties.length === 0 ? (
          <div className="rounded-lg border border-dashed border-gray-300 p-8 text-center">
            <p className="text-sm text-gray-500">
              Henüz ilan bulunmuyor. Önce portföyünüze ilan ekleyin.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {properties.map((property) => {
              const isSelected = selectedProperties.includes(property.id);
              return (
                <div
                  key={property.id}
                  className="relative cursor-pointer"
                  onClick={() => toggleProperty(property.id)}
                >
                  <div className={cn("transition-all", isSelected ? "ring-2 ring-orange-600 ring-offset-2 rounded-lg opacity-100" : "opacity-80 hover:opacity-100")}>
                    <PropertyCard property={property} />
                  </div>
                  {isSelected && (
                    <div className="absolute -top-2 -right-2 h-6 w-6 bg-orange-600 rounded-full flex items-center justify-center text-white shadow-sm">
                      <Check className="h-4 w-4" />
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Theme Selection */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-medium text-gray-900">Tema Seçimi</h3>
          <p className="text-sm text-gray-500">
            Vitrin sayfanızın görünümünü kişiselleştirin
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-3">
          {THEMES.map((t) => {
            const isSelected = theme === t.id;
            return (
              <Card
                key={t.id}
                className={cn(
                  "cursor-pointer transition-all hover:border-orange-200",
                  isSelected ? "border-orange-600 ring-1 ring-orange-600 bg-orange-50/30" : ""
                )}
                onClick={() => setTheme(t.id)}
              >
                <CardContent className="p-4 flex flex-col items-center justify-center text-center gap-3">
                  <div
                    className={cn(
                      "w-12 h-12 rounded-full border-4 shadow-sm",
                      t.background === "dark" ? "bg-gray-900" : "bg-white"
                    )}
                    style={{ borderColor: t.primary_color }}
                  />
                  <div>
                    <p className="font-medium text-gray-900">{t.label}</p>
                    <p className="text-xs text-gray-500">
                      {t.background === "dark" ? "Koyu" : "Açık"} Tema, {t.layout === "grid" ? "Grid" : "Liste"} Görünüm
                    </p>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-end gap-3 pt-6 border-t">
        <Button
          type="button"
          variant="outline"
          onClick={() => router.push("/network")}
        >
          İptal
        </Button>
        <Button
          type="submit"
          disabled={isSubmitting || selectedProperties.length === 0}
          className="bg-orange-600 hover:bg-orange-700 text-white min-w-[120px]"
        >
          {isSubmitting ? (
            <Loader2 className="h-4 w-4 animate-spin mr-2" />
          ) : (
            <Check className="h-4 w-4 mr-2" />
          )}
          {initialData ? "Kaydet" : "Oluştur"}
        </Button>
      </div>
    </form>
  );
}
