'use client';

import { createContext, useContext } from 'react';
import type { Map } from 'maplibre-gl';

interface MapContextType {
  map: Map | null;
}

export const MapContext = createContext<MapContextType | undefined>(undefined);

export function useMap() {
  const context = useContext(MapContext);
  if (context === undefined) {
    throw new Error('useMap must be used within a MapProvider (BaseMap)');
  }

  const flyTo = (center: [number, number], zoom?: number) => {
    if (context.map) {
      context.map.flyTo({
        center,
        zoom: zoom ?? context.map.getZoom(),
        essential: true,
      });
    }
  };

  const fitBounds = (bounds: [number, number, number, number], options = {}) => {
    if (context.map) {
      // maplibre-gl expects LngLatBoundsLike, which can be [w, s, e, n]
      context.map.fitBounds(bounds as [number, number, number, number], options);
    }
  };

  return {
    map: context.map,
    flyTo,
    fitBounds,
  };
}
