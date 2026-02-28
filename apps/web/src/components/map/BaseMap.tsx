'use client';

import React, { useRef, useEffect, useState, useImperativeHandle, forwardRef } from 'react';
import maplibregl, { Map as MapType, AttributionControl, StyleSpecification } from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { MapContext } from '@/hooks/use-map';
import { cn } from '@/lib/utils';
import { ZoomIn, ZoomOut, Navigation } from 'lucide-react';

// Default Istanbul coordinates
const DEFAULT_CENTER: [number, number] = [28.9784, 41.0082];
const DEFAULT_ZOOM = 10;

// OSM Raster Style
const OSM_STYLE: StyleSpecification = {
  version: 8,
  sources: {
    'osm-tiles': {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '&copy; OpenStreetMap Contributors',
    },
  },
  layers: [
    {
      id: 'simple-tiles',
      type: 'raster',
      source: 'osm-tiles',
      minzoom: 0,
      maxzoom: 22,
    },
  ],
};

export interface BaseMapProps {
  center?: [number, number]; // [lng, lat]
  zoom?: number;
  className?: string;
  children?: React.ReactNode;
  onMapReady?: (map: MapType) => void;
}

export const BaseMap = forwardRef<HTMLDivElement, BaseMapProps>(
  ({ center = DEFAULT_CENTER, zoom = DEFAULT_ZOOM, className, children, onMapReady }, ref) => {
    const mapContainer = useRef<HTMLDivElement>(null);
    const [mapInstance, setMapInstance] = useState<MapType | null>(null);

    // Forward the ref if provided, otherwise use internal ref
    useImperativeHandle(ref, () => mapContainer.current as HTMLDivElement);

    useEffect(() => {
      if (mapInstance) return; // Initialize only once

      if (!mapContainer.current) return;

      const map = new maplibregl.Map({
        container: mapContainer.current,
        style: OSM_STYLE,
        center: center,
        zoom: zoom,
        attributionControl: false, // We'll add a custom one or rely on the source attribution
      });

      // Add default attribution control to bottom-right (compact)
      map.addControl(new AttributionControl({ compact: true }), 'bottom-right');
      
      // Wait for load event
      map.on('load', () => {
        setMapInstance(map);
        if (onMapReady) onMapReady(map);
      });

      return () => {
        map.remove();
      };
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Empty dependency array to run once on mount

    // Update center/zoom if props change (optional, but good practice)
    useEffect(() => {
      if (!mapInstance) return;
      // We don't want to fly on every render, only if props change significantly
      // For now, let's keep it simple: initial load only, or explicit control via hook
    }, [center, zoom, mapInstance]);

    // Custom Controls Handlers
    const handleZoomIn = () => {
      mapInstance?.zoomIn();
    };

    const handleZoomOut = () => {
      mapInstance?.zoomOut();
    };

    const handleLocate = () => {
      if ('geolocation' in navigator) {
        navigator.geolocation.getCurrentPosition(
          (position) => {
            const { longitude, latitude } = position.coords;
            mapInstance?.flyTo({
              center: [longitude, latitude],
              zoom: 14,
            });
            // Add a marker for user location if needed, or just fly there
          },
          (error) => {
            console.error('Error getting location', error);
          }
        );
      }
    };

    return (
      <div className={cn("relative w-full h-full min-h-[400px] overflow-hidden rounded-lg bg-gray-100", className)}>
        <div ref={mapContainer} className="absolute inset-0 w-full h-full" />
        
        {/* Custom Controls UI - Top Right or Bottom Right */}
        <div className="absolute bottom-6 right-2 flex flex-col gap-2 z-10">
           <button
            onClick={handleLocate}
            className="p-2 bg-white rounded-md shadow-md hover:bg-gray-50 border border-gray-200 text-gray-700 transition-colors cursor-pointer"
            title="Konumumu Bul"
            type="button"
          >
            <Navigation className="w-5 h-5" />
          </button>
          <div className="flex flex-col rounded-md shadow-md border border-gray-200 bg-white overflow-hidden">
            <button
              onClick={handleZoomIn}
              className="p-2 hover:bg-gray-50 border-b border-gray-200 text-gray-700 transition-colors cursor-pointer"
              title="Yakınlaş"
              type="button"
            >
              <ZoomIn className="w-5 h-5" />
            </button>
            <button
              onClick={handleZoomOut}
              className="p-2 hover:bg-gray-50 text-gray-700 transition-colors cursor-pointer"
              title="Uzaklaş"
              type="button"
            >
              <ZoomOut className="w-5 h-5" />
            </button>
          </div>
        </div>

        <MapContext.Provider value={{ map: mapInstance }}>
          {mapInstance && children}
        </MapContext.Provider>
      </div>
    );
  }
);

BaseMap.displayName = "BaseMap";
