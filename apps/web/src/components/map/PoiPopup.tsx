'use client';

import React from 'react';
import { MapPin, Clock, Ruler, X } from 'lucide-react';
import type { PoiFeature, PoiCategory } from './PoiLayer';

// --- Tipler ---

export interface PoiPopupProps {
  poi: PoiFeature;
  category: PoiCategory;
  /** Kullanıcının seçili mülkünün koordinatı [lng, lat]. Verilirse mesafe hesaplanır. */
  propertyCoordinates?: [number, number];
  onClose?: () => void;
}

// --- Haversine mesafe hesaplama ---

/** Dünya yüzeyi üzerinde iki nokta arası mesafeyi km olarak hesaplar (Haversine formülü) */
export function haversineDistance(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
): number {
  const R = 6371; // Dünya yarıçapı (km)
  const dLat = ((lat2 - lat1) * Math.PI) / 180;
  const dLon = ((lon2 - lon1) * Math.PI) / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos((lat1 * Math.PI) / 180) *
      Math.cos((lat2 * Math.PI) / 180) *
      Math.sin(dLon / 2) *
      Math.sin(dLon / 2);
  return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
}

/** Mesafeyi okunabilir formata çevirir (<1km → metre, >=1km → km) */
function formatDistance(km: number): string {
  if (km < 1) {
    return `${Math.round(km * 1000)} m`;
  }
  return `${km.toFixed(1)} km`;
}

/** Yürüyüş süresi tahmini (80 m/dk varsayımı) */
function estimateWalkingMinutes(km: number): number {
  const meters = km * 1000;
  return Math.ceil(meters / 80);
}

// --- Kategori etiketleri ---

const CATEGORY_LABELS: Record<PoiCategory, string> = {
  school: 'Okul',
  metro: 'Ulaşım',
  hospital: 'Sağlık',
};

const CATEGORY_COLORS: Record<PoiCategory, string> = {
  school: '#3B82F6',
  metro: '#8B5CF6',
  hospital: '#EF4444',
};

/** POI alt tip etiketlerini Türkçeye çevirir */
function getTypeLabel(type: string): string {
  const labels: Record<string, string> = {
    ilkokul: 'İlkokul',
    ortaokul: 'Ortaokul',
    lise: 'Lise',
    universite: 'Üniversite',
    metro: 'Metro',
    metrobus: 'Metrobüs',
    tramvay: 'Tramvay',
    devlet: 'Devlet Hastanesi',
    ozel: 'Özel Hastane',
    aile_sagligi: 'Aile Sağlığı Merkezi',
  };
  return labels[type] ?? type;
}

// --- Bileşen ---

/**
 * PoiPopup — POI tıklandığında gösterilen popup.
 *
 * Gösterir:
 * - POI adı ve tipi
 * - Adres veya hat bilgisi
 * - Seçili mülke olan mesafe (varsa)
 * - Yürüme süresi tahmini
 *
 * Stili: PropertyPopup ile tutarlı (bg-white, shadow, rounded)
 */
export const PoiPopup: React.FC<PoiPopupProps> = ({
  poi,
  category,
  propertyCoordinates,
  onClose,
}) => {
  // Mesafe hesaplama (property seçiliyse)
  const distanceKm =
    propertyCoordinates
      ? haversineDistance(
          poi.coordinates[1], // lat
          poi.coordinates[0], // lng
          propertyCoordinates[1],
          propertyCoordinates[0],
        )
      : null;

  const walkingMinutes = distanceKm !== null ? estimateWalkingMinutes(distanceKm) : null;

  const categoryColor = CATEGORY_COLORS[category];

  return (
    <div className="w-64 bg-white rounded-lg shadow-lg overflow-hidden text-sm font-sans">
      {/* Başlık */}
      <div className="p-3 border-b border-gray-100 flex items-start justify-between gap-2">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-1.5 mb-0.5">
            {/* Kategori renk noktası */}
            <span
              className="flex-shrink-0 w-2.5 h-2.5 rounded-full"
              style={{ backgroundColor: categoryColor }}
            />
            <span className="text-xs font-medium text-gray-500">
              {CATEGORY_LABELS[category]}
            </span>
          </div>
          <h3 className="font-semibold text-gray-900 truncate" title={poi.name}>
            {poi.name}
          </h3>
        </div>

        {onClose && (
          <button
            type="button"
            onClick={onClose}
            className="flex-shrink-0 p-0.5 text-gray-400 hover:text-gray-600 transition-colors cursor-pointer"
            title="Kapat"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Detaylar */}
      <div className="p-3 space-y-2 text-gray-600">
        {/* Tip bilgisi */}
        <div className="flex items-center gap-1.5">
          <MapPin className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
          <span>{getTypeLabel(poi.type)}</span>
        </div>

        {/* Adres veya hat bilgisi */}
        {poi.address && (
          <p className="text-xs text-gray-500 pl-5">{poi.address}</p>
        )}
        {poi.line && (
          <p className="text-xs text-gray-500 pl-5">Hat: {poi.line}</p>
        )}

        {/* Mesafe bilgisi */}
        {distanceKm !== null && (
          <div className="mt-2 pt-2 border-t border-gray-100 space-y-1.5">
            <div className="flex items-center gap-1.5">
              <Ruler className="w-3.5 h-3.5 text-blue-500 flex-shrink-0" />
              <span className="font-medium text-gray-900">
                {formatDistance(distanceKm)}
              </span>
              <span className="text-xs text-gray-400">uzaklıkta</span>
            </div>

            {walkingMinutes !== null && (
              <div className="flex items-center gap-1.5">
                <Clock className="w-3.5 h-3.5 text-gray-400 flex-shrink-0" />
                <span className="text-gray-600">
                  Yürüme ~{walkingMinutes} dk
                </span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
