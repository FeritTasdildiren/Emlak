'use client';

import React from 'react';
import { ArrowRight, BedDouble, Square, Tag } from 'lucide-react';

export interface PropertyPopupProps {
  id: string;
  title: string;
  price: number;
  rooms: string;
  sqm: number;
  district: string;
}

export const PropertyPopup: React.FC<PropertyPopupProps> = ({ 
  id,
  title, 
  price, 
  rooms, 
  sqm, 
  district 
}) => {
  const formatPrice = (value: number) => {
    return new Intl.NumberFormat('tr-TR', { 
      style: 'currency', 
      currency: 'TRY', 
      maximumFractionDigits: 0 
    }).format(value);
  };

  return (
    <div className="w-64 bg-white rounded-lg shadow-lg overflow-hidden text-sm font-sans">
      <div className="p-3 border-b border-gray-100">
        <h3 className="font-semibold text-gray-900 truncate" title={title}>{title}</h3>
        <p className="text-xs text-gray-500 mt-0.5">{district}</p>
      </div>
      
      <div className="p-3 grid grid-cols-2 gap-2 text-gray-600">
        <div className="flex items-center gap-1.5 col-span-2" title="Fiyat">
          <Tag className="w-3.5 h-3.5 text-blue-500" />
          <span className="font-medium text-gray-900 text-base">{formatPrice(price)}</span>
        </div>
        <div className="flex items-center gap-1.5" title="m²">
             <Square className="w-3.5 h-3.5 text-gray-400" />
             <span>{sqm} m²</span>
        </div>
        <div className="flex items-center gap-1.5" title="Oda Sayısı">
             <BedDouble className="w-3.5 h-3.5 text-gray-400" />
             <span>{rooms}</span>
        </div>
      </div>

      <div className="bg-gray-50 px-3 py-2 border-t border-gray-100 flex justify-end">
        <a 
          href={`/properties/${id}`} 
          className="text-xs font-medium text-blue-600 hover:text-blue-700 flex items-center gap-1 transition-colors"
        >
          Detay Gör
          <ArrowRight className="w-3 h-3" />
        </a>
      </div>
    </div>
  );
};
