"use client";

import type { Property } from "@/types/property";
import { Badge } from "@/components/ui/badge";
import { cn, formatCurrency, formatDate } from "@/lib/utils";
import { Home, Building2, LandPlot, MapPin, Ruler } from "lucide-react";

const statusConfig: Record<
  Property["status"],
  { label: string; variant: "success" | "default" | "warning" | "secondary" }
> = {
  active: { label: "Aktif", variant: "success" },
  sold: { label: "Satıldı", variant: "default" },
  rented: { label: "Kiralandı", variant: "warning" },
  draft: { label: "Taslak", variant: "secondary" },
};

const typeConfig: Record<
  Property["property_type"],
  { label: string; icon: typeof Home }
> = {
  daire: { label: "Daire", icon: Home },
  villa: { label: "Villa", icon: Home },
  ofis: { label: "Ofis", icon: Building2 },
  arsa: { label: "Arsa", icon: LandPlot },
  dukkan: { label: "Dükkan", icon: Building2 },
};

interface PropertyCardProps {
  property: Property;
  onClick?: (property: Property) => void;
}

export function PropertyCard({ property, onClick }: PropertyCardProps) {
  const status = statusConfig[property.status];
  const type = typeConfig[property.property_type];
  const TypeIcon = type.icon;

  return (
    <div
      onClick={() => onClick?.(property)}
      className={cn(
        "group rounded-lg border bg-white p-4 shadow-sm transition-all hover:shadow-md",
        onClick && "cursor-pointer"
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3 min-w-0">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
            <TypeIcon className="h-5 w-5" />
          </div>
          <div className="min-w-0">
            <h3 className="truncate font-medium text-gray-900 group-hover:text-blue-600 transition-colors">
              {property.title}
            </h3>
            <div className="mt-1 flex items-center gap-1 text-sm text-gray-500">
              <MapPin className="h-3.5 w-3.5 shrink-0" />
              <span className="truncate">
                {property.district}, {property.city}
              </span>
            </div>
          </div>
        </div>
        <Badge variant={status.variant} className="shrink-0">
          {status.label}
        </Badge>
      </div>

      <div className="mt-4 flex items-center justify-between">
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Ruler className="h-3.5 w-3.5" />
            <span>{property.area_sqm} m²</span>
          </div>
          {property.room_count && (
            <span>{property.room_count} Oda</span>
          )}
          {property.floor != null && (
            <span>Kat {property.floor}</span>
          )}
        </div>
        <div className="text-right">
          <p className="font-semibold text-gray-900">
            {formatCurrency(property.price)}
          </p>
          <p className="text-xs text-gray-400">
            {property.listing_type === "kiralik" ? "/ay" : ""}
          </p>
        </div>
      </div>

      <div className="mt-3 flex items-center justify-between border-t pt-3 text-xs text-gray-400">
        <span>{type.label}</span>
        <span>{formatDate(property.created_at)}</span>
      </div>
    </div>
  );
}
