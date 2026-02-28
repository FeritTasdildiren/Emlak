'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import { TrendingUp, TrendingDown, Users, DollarSign, Activity, AlertTriangle } from 'lucide-react';

export interface AreaAnalysisCardProps {
  regionName: string;
  demographics: { 
    population: number; 
    density?: string 
  };
  pricing: { 
    avgSalePrice: number; 
    avgRentPrice?: number; 
    changePercentage?: number 
  };
  investment: { 
    roi?: number; 
    amortizationYears?: number; 
    score?: number 
  };
  risk?: { 
    level: 'low' | 'medium' | 'high' | 'critical'; 
    pgaValue?: number; 
    groundClass?: string 
  };
  className?: string;
}

export const AreaAnalysisCard: React.FC<AreaAnalysisCardProps> = ({
  regionName,
  demographics,
  pricing,
  investment,
  risk,
  className
}) => {
  const formatNumber = (num: number) => new Intl.NumberFormat('tr-TR').format(num);
  const formatCurrency = (num: number) => new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(num);

  const getRiskColor = (level: string) => {
    switch(level) {
      case 'low': return 'bg-green-100 text-green-700 border-green-200';
      case 'medium': return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'high': return 'bg-orange-100 text-orange-700 border-orange-200';
      case 'critical': return 'bg-red-100 text-red-700 border-red-200';
      default: return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getRiskLabel = (level: string) => {
    switch(level) {
      case 'low': return 'Düşük Risk';
      case 'medium': return 'Orta Risk';
      case 'high': return 'Yüksek Risk';
      case 'critical': return 'Kritik Risk';
      default: return 'Belirsiz';
    }
  };

  return (
    <div className={cn("bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden font-inter", className)}>
      <div className="px-4 py-3 border-b border-slate-100 bg-slate-50 flex justify-between items-center">
        <h3 className="font-semibold text-slate-800">{regionName} Bölge Analizi</h3>
        {risk && (
          <span className={cn("text-xs px-2 py-1 rounded-full border font-medium", getRiskColor(risk.level))}>
            {getRiskLabel(risk.level)}
          </span>
        )}
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-slate-100">
        {/* Demographics */}
        <div className="bg-white p-4 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-slate-500 mb-1">
            <Users className="w-4 h-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Demografi</span>
          </div>
          <div className="flex justify-between items-end">
             <div>
                <p className="text-2xl font-bold text-slate-900">{formatNumber(demographics.population)}</p>
                <p className="text-xs text-slate-500">Nüfus</p>
             </div>
             {demographics.density && (
               <div className="text-right">
                  <p className="text-sm font-semibold text-slate-700">{demographics.density}</p>
                  <p className="text-xs text-slate-500">Yoğunluk</p>
               </div>
             )}
          </div>
        </div>

        {/* Pricing */}
        <div className="bg-white p-4 flex flex-col gap-2">
          <div className="flex items-center gap-2 text-slate-500 mb-1">
            <DollarSign className="w-4 h-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Fiyat Analizi</span>
          </div>
          <div className="flex justify-between items-end">
             <div>
                <p className="text-lg font-bold text-slate-900">{formatCurrency(pricing.avgSalePrice)}</p>
                <p className="text-xs text-slate-500">Ort. m² Satış</p>
             </div>
             {pricing.changePercentage !== undefined && (
               <div className={cn("flex items-center gap-1 text-sm font-bold", pricing.changePercentage >= 0 ? "text-green-600" : "text-red-600")}>
                  {pricing.changePercentage >= 0 ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                  <span>%{Math.abs(pricing.changePercentage)}</span>
               </div>
             )}
          </div>
        </div>

        {/* Investment */}
        <div className="bg-white p-4 flex flex-col gap-2">
           <div className="flex items-center gap-2 text-slate-500 mb-1">
            <Activity className="w-4 h-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Yatırım</span>
          </div>
          <div className="flex justify-between items-center">
             <div className="space-y-1">
                {investment.roi && (
                   <p className="text-sm text-slate-700">
                      <span className="text-slate-500">Getiri:</span> <span className="font-semibold">%{investment.roi}</span>
                   </p>
                )}
                {investment.amortizationYears && (
                   <p className="text-sm text-slate-700">
                      <span className="text-slate-500">Amortisman:</span> <span className="font-semibold">{investment.amortizationYears} Yıl</span>
                   </p>
                )}
             </div>
             {investment.score && (
               <div className="relative w-12 h-12 flex items-center justify-center rounded-full border-4 border-blue-100 bg-blue-50">
                  <span className="text-blue-700 font-bold text-sm">{investment.score}</span>
               </div>
             )}
          </div>
        </div>

        {/* Risk Detail */}
        <div className="bg-white p-4 flex flex-col gap-2">
           <div className="flex items-center gap-2 text-slate-500 mb-1">
            <AlertTriangle className="w-4 h-4" />
            <span className="text-xs font-medium uppercase tracking-wider">Risk Faktörleri</span>
          </div>
          <div className="space-y-2 mt-1">
             <div className="flex justify-between text-sm">
                <span className="text-slate-500">Zemin Sınıfı</span>
                <span className="font-medium text-slate-900">{risk?.groundClass || '-'}</span>
             </div>
             <div className="flex justify-between text-sm">
                <span className="text-slate-500">PGA Değeri</span>
                <span className="font-medium text-slate-900">{risk?.pgaValue || '-'}</span>
             </div>
          </div>
        </div>
      </div>
    </div>
  );
};
