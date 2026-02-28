'use client';

import React from 'react';
import dynamic from 'next/dynamic';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';
import type { Map } from 'maplibre-gl';

// Dynamically import BaseMap with no SSR
const BaseMap = dynamic(() => import('./BaseMap').then((mod) => mod.BaseMap), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center w-full h-full min-h-[400px] bg-gray-100 rounded-lg">
      <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      <span className="ml-2 text-gray-500">Harita Yükleniyor...</span>
    </div>
  ),
});

interface MapContainerProps {
  className?: string;
  children?: React.ReactNode;
  center?: [number, number];
  zoom?: number;
  onMapReady?: (map: Map) => void;
}

export const MapContainer: React.FC<MapContainerProps> = ({ 
  className, 
  children,
  center,
  zoom,
  onMapReady 
}) => {
  return (
    <div className={cn("relative w-full h-full min-h-[400px]", className)}>
      <BaseMap center={center} zoom={zoom} onMapReady={onMapReady}>
        {children}
      </BaseMap>
    </div>
  );
};
