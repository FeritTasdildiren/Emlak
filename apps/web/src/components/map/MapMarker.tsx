'use client';

import React, { useEffect, useRef, useState } from 'react';
import { createPortal } from 'react-dom';
import maplibregl from 'maplibre-gl';
import { useMap } from '@/hooks/use-map';

interface MapMarkerProps {
  latitude: number;
  longitude: number;
  color?: string;
  onClick?: () => void;
  children?: React.ReactNode; // Popup content
}

export const MapMarker: React.FC<MapMarkerProps> = ({ 
  latitude, 
  longitude, 
  color = '#3B82F6', 
  onClick, 
  children 
}) => {
  const { map } = useMap();
  const [marker, setMarker] = useState<maplibregl.Marker | null>(null);
  const popupContainerRef = useRef<HTMLDivElement | null>(null);

  // Initialize marker only once when map is ready
  useEffect(() => {
    if (!map) return;

    // Create marker
    const newMarker = new maplibregl.Marker({ color })
      .setLngLat([longitude, latitude])
      .addTo(map);

    // Add click handler if provided
    if (onClick) {
      newMarker.getElement().addEventListener('click', () => {
        // e.stopPropagation(); // Might interfere with popup opening if both exist
        onClick();
      });
      newMarker.getElement().style.cursor = 'pointer';
    }

    // Prepare popup if children exist
    if (children) {
      const popupContainer = document.createElement('div');
      popupContainer.className = 'map-popup-content'; // Add a class for styling if needed
      popupContainerRef.current = popupContainer;

      const popup = new maplibregl.Popup({ offset: 25 })
        .setDOMContent(popupContainer);

      newMarker.setPopup(popup);
    }

    setMarker(newMarker);

    return () => {
      newMarker.remove();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [map]); // Re-create only if map instance changes (init)

  // Update position dynamically
  useEffect(() => {
    if (marker) {
      marker.setLngLat([longitude, latitude]);
    }
  }, [marker, latitude, longitude]);

  // Render popup content via Portal
  if (!marker || !children || !popupContainerRef.current) {
    return null;
  }

  return createPortal(
    children,
    popupContainerRef.current
  );
};
