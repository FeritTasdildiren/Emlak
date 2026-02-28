'use client';

import React from 'react';
import { MapMarker } from './MapMarker';
import { PropertyPopup } from './PropertyPopup';

export interface Property {
  id: string;
  lat: number;
  lon: number;
  price: number;
  rooms: string;
  sqm: number;
  title: string;
  district: string;
}

interface PropertyMarkerLayerProps {
  properties: Property[];
  onMarkerClick?: (property: Property) => void;
}

export const PropertyMarkerLayer: React.FC<PropertyMarkerLayerProps> = ({ 
  properties, 
  onMarkerClick 
}) => {
  // Determine color based on price range
  const getMarkerColor = (price: number): string => {
    if (price < 3000000) return '#10B981'; // Green (< 3M)
    if (price < 7000000) return '#3B82F6'; // Blue (3M - 7M)
    if (price < 15000000) return '#F59E0B'; // Orange (7M - 15M)
    return '#EF4444'; // Red (> 15M)
  };

  return (
    <>
      {properties.map((property) => (
        <MapMarker
          key={property.id}
          latitude={property.lat}
          longitude={property.lon}
          color={getMarkerColor(property.price)}
          onClick={() => onMarkerClick?.(property)}
        >
          <PropertyPopup
            id={property.id}
            title={property.title}
            price={property.price}
            rooms={property.rooms}
            sqm={property.sqm}
            district={property.district}
          />
        </MapMarker>
      ))}
    </>
  );
};
