'use client';

import React from 'react';
import { cn } from '@/lib/utils';

// --- Tipler ---

export interface LayerInfo {
  id: string;
  label: string;
  icon: React.ReactNode;
  color: string;
  visible: boolean;
  count?: number;
}

export interface LayerControlProps {
  layers: LayerInfo[];
  onToggle: (layerId: string) => void;
}

// --- Bileşen ---

/**
 * LayerControl — Harita sağ üst köşesine overlay olarak katman toggle butonları.
 *
 * - pointer-events-none wrapper + pointer-events-auto child → Harita etkileşimi korunur
 * - Mobilde compact (sadece ikon), desktop'ta ikon+label
 * - Aktif katman: renkli border + opak, pasif: gri + yarı saydam
 */
export const LayerControl: React.FC<LayerControlProps> = ({ layers, onToggle }) => {
  return (
    // pointer-events-none wrapper: haritanın altına tıklama iletilir
    <div className="absolute top-3 right-3 z-20 pointer-events-none">
      {/* pointer-events-auto child: sadece bu alan tıklanabilir */}
      <div className="pointer-events-auto bg-white rounded-lg shadow-md border border-gray-200 overflow-hidden">
        {/* Başlık — sadece desktop'ta görünür */}
        <div className="hidden md:block px-3 py-2 border-b border-gray-100 bg-gray-50">
          <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
            Katmanlar
          </span>
        </div>

        {/* Katman toggle listesi */}
        <div className="flex flex-col">
          {layers.map((layer, index) => (
            <button
              key={layer.id}
              type="button"
              onClick={() => onToggle(layer.id)}
              className={cn(
                'flex items-center gap-2 px-3 py-2 transition-all cursor-pointer',
                'hover:bg-gray-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400',
                // Aktif / pasif stiller
                layer.visible
                  ? 'opacity-100'
                  : 'opacity-50',
                // Alt border (son eleman hariç)
                index < layers.length - 1 && 'border-b border-gray-100',
              )}
              title={`${layer.label} ${layer.visible ? 'gizle' : 'göster'}`}
            >
              {/* Renk göstergesi */}
              <span
                className={cn(
                  'flex-shrink-0 w-3 h-3 rounded-full border-2',
                  layer.visible ? 'border-current' : 'border-gray-300 bg-gray-200',
                )}
                style={layer.visible ? { backgroundColor: layer.color, borderColor: layer.color } : undefined}
              />

              {/* İkon */}
              <span className="flex-shrink-0 text-gray-600">
                {layer.icon}
              </span>

              {/* Label — mobilde gizli */}
              <span className="hidden md:inline text-sm text-gray-700 whitespace-nowrap">
                {layer.label}
              </span>

              {/* Adet bilgisi (opsiyonel) */}
              {layer.count !== undefined && (
                <span className="hidden md:inline text-xs text-gray-400 ml-auto">
                  {layer.count}
                </span>
              )}

              {/* Toggle göstergesi */}
              <span
                className={cn(
                  'ml-auto md:ml-2 flex-shrink-0 w-8 h-4 rounded-full transition-colors relative',
                  layer.visible ? 'bg-blue-500' : 'bg-gray-300',
                )}
              >
                <span
                  className={cn(
                    'absolute top-0.5 w-3 h-3 rounded-full bg-white shadow-sm transition-transform',
                    layer.visible ? 'translate-x-4' : 'translate-x-0.5',
                  )}
                />
              </span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};
