'use client';

import { useEffect, useCallback } from 'react';
import type { Map as MapType, MapMouseEvent, GeoJSONSource, GeoJSONSourceSpecification } from 'maplibre-gl';

import schoolsData from '@/data/poi/istanbul_schools.json';
import metroData from '@/data/poi/istanbul_metro.json';
import hospitalsData from '@/data/poi/istanbul_hospitals.json';

// --- Tipler ---

/** POI kategorileri */
export type PoiCategory = 'school' | 'metro' | 'hospital';

/** Tıklama callback'ine gönderilen veri */
export interface PoiFeature {
  name: string;
  type: string;
  address?: string;
  line?: string;
  coordinates: [number, number]; // [lng, lat]
}

export interface PoiLayerProps {
  map: MapType | null;
  category: PoiCategory;
  visible: boolean;
  onPoiClick?: (poi: PoiFeature) => void;
}

// --- Yardımcı sabitler ---

const CATEGORY_COLORS: Record<PoiCategory, string> = {
  school: '#3B82F6',   // blue-500
  metro: '#8B5CF6',    // violet-500
  hospital: '#EF4444', // red-500
};

/**
 * JSON import'lar TypeScript'te literal type yerine widened type üretir
 * (ör. "Feature" yerine string). MapLibre'ın GeoJSON tipi strict olduğu
 * için GeoJSONSourceSpecification['data'] tipine cast ediyoruz.
 * Runtime'da veri doğru GeoJSON formatında — bu güvenli bir cast.
 */
type SourceData = GeoJSONSourceSpecification['data'];

const CATEGORY_DATA: Record<PoiCategory, SourceData> = {
  school: schoolsData as unknown as SourceData,
  metro: metroData as unknown as SourceData,
  hospital: hospitalsData as unknown as SourceData,
};

/**
 * Verilen kategori için source ve layer id'lerini döndürür.
 * MapLibre'da source/layer isimleri unique olmalı.
 */
function getIds(category: PoiCategory) {
  return {
    sourceId: `poi-source-${category}`,
    layerId: `poi-layer-${category}`,
  };
}

// --- Bileşen ---

/**
 * PoiLayer — MapLibre haritasına GeoJSON source + circle layer ekler.
 *
 * Her kategori (school, metro, hospital) farklı renkte circle ile gösterilir.
 * Performans: DOM marker yerine GeoJSON source + CircleLayer kullanır.
 * visible prop ile katman açılıp kapatılır.
 * Tıklama eventi ile POI bilgisi callback'e gönderilir.
 */
export const PoiLayer: React.FC<PoiLayerProps> = ({ map, category, visible, onPoiClick }) => {
  const { sourceId, layerId } = getIds(category);
  const color = CATEGORY_COLORS[category];
  const data = CATEGORY_DATA[category];

  // Tıklama handler — useCallback ile stabil referans
  const handleClick = useCallback(
    (e: MapMouseEvent) => {
      if (!onPoiClick) return;

      // MapLibre queryRenderedFeatures ile tıklanan feature'ı bul
      const features = e.target.queryRenderedFeatures(e.point, { layers: [layerId] });
      if (!features || features.length === 0) return;

      const feature = features[0];
      const geometry = feature.geometry;
      if (geometry.type !== 'Point') return;

      const props = feature.properties as Record<string, unknown>;

      const poi: PoiFeature = {
        name: (props.name as string) ?? '',
        type: (props.type as string) ?? '',
        address: props.address as string | undefined,
        line: props.line as string | undefined,
        coordinates: geometry.coordinates as [number, number],
      };

      onPoiClick(poi);
    },
    [onPoiClick, layerId],
  );

  // Source + Layer ekleme / kaldırma
  useEffect(() => {
    if (!map) return;

    // Harita style yüklenmeden source/layer eklenemez
    const addSourceAndLayer = () => {
      // Zaten varsa ekleme (hot-reload güvenliği)
      if (map.getSource(sourceId)) return;

      map.addSource(sourceId, {
        type: 'geojson',
        data: data,
      });

      map.addLayer({
        id: layerId,
        type: 'circle',
        source: sourceId,
        paint: {
          'circle-radius': 6,
          'circle-color': color,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
        },
        layout: {
          visibility: visible ? 'visible' : 'none',
        },
      });

      // Tıklama için pointer cursor
      map.on('mouseenter', layerId, () => {
        map.getCanvas().style.cursor = 'pointer';
      });
      map.on('mouseleave', layerId, () => {
        map.getCanvas().style.cursor = '';
      });
    };

    // Style zaten yüklüyse hemen ekle, değilse bekle
    if (map.isStyleLoaded()) {
      addSourceAndLayer();
    } else {
      map.on('load', addSourceAndLayer);
    }

    return () => {
      // Cleanup: layer ve source'u kaldır
      try {
        if (map.getLayer(layerId)) {
          map.removeLayer(layerId);
        }
        if (map.getSource(sourceId)) {
          map.removeSource(sourceId);
        }
      } catch {
        // Map zaten destroy edilmiş olabilir — sessizce geç
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map]);

  // Visibility değişikliği
  useEffect(() => {
    if (!map) return;

    try {
      if (map.getLayer(layerId)) {
        map.setLayoutProperty(layerId, 'visibility', visible ? 'visible' : 'none');
      }
    } catch {
      // Layer henüz eklenmemiş olabilir
    }
  }, [map, visible, layerId]);

  // Tıklama event binding
  useEffect(() => {
    if (!map) return;

    map.on('click', layerId, handleClick);

    return () => {
      try {
        map.off('click', layerId, handleClick);
      } catch {
        // Map destroy edilmiş olabilir
      }
    };
  }, [map, layerId, handleClick]);

  // Data güncellemesi (GeoJSON değişirse)
  useEffect(() => {
    if (!map) return;

    try {
      const source = map.getSource(sourceId) as GeoJSONSource | undefined;
      if (source) {
        source.setData(data as GeoJSONSourceSpecification['data']);
      }
    } catch {
      // Source henüz eklenmemiş olabilir
    }
  }, [map, sourceId, data]);

  // Bu bileşen DOM render etmez — sadece MapLibre side-effect'leri yönetir
  return null;
};
