"use client";

import { Suspense, useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import {
  ArrowLeft,
  X,
  AlertCircle,
  BarChart3
} from "lucide-react";

// Recharts ağır kütüphane — lazy load ile bundle'dan ayır
const CompareChart = dynamic(
  () => import("./compare-chart"),
  { loading: () => <div className="h-[400px] w-full animate-pulse bg-gray-100 rounded-lg" /> }
);

import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { useAreaCompare } from "@/hooks/use-area-compare";
import Link from "next/link";
import { cn } from "@/lib/utils";

const ISTANBUL_DISTRICTS = [
  { value: "Adalar", label: "Adalar" },
  { value: "Arnavutkoy", label: "Arnavutköy" },
  { value: "Atasehir", label: "Ataşehir" },
  { value: "Avcilar", label: "Avcılar" },
  { value: "Bagcilar", label: "Bağcılar" },
  { value: "Bahcelievler", label: "Bahçelievler" },
  { value: "Bakirkoy", label: "Bakırköy" },
  { value: "Basaksehir", label: "Başakşehir" },
  { value: "Bayrampasa", label: "Bayrampaşa" },
  { value: "Besiktas", label: "Beşiktaş" },
  { value: "Beykoz", label: "Beykoz" },
  { value: "Beylikduzu", label: "Beylikdüzü" },
  { value: "Beyoglu", label: "Beyoğlu" },
  { value: "Buyukcekmece", label: "Büyükçekmece" },
  { value: "Catalca", label: "Çatalca" },
  { value: "Cekmekoy", label: "Çekmeköy" },
  { value: "Esenler", label: "Esenler" },
  { value: "Esenyurt", label: "Esenyurt" },
  { value: "Eyupsultan", label: "Eyüpsultan" },
  { value: "Fatih", label: "Fatih" },
  { value: "Gaziosmanpasa", label: "Gaziosmanpaşa" },
  { value: "Gungoren", label: "Güngören" },
  { value: "Kadikoy", label: "Kadıköy" },
  { value: "Kagithane", label: "Kağıthane" },
  { value: "Kartal", label: "Kartal" },
  { value: "Kucukcekmece", label: "Küçükçekmece" },
  { value: "Maltepe", label: "Maltepe" },
  { value: "Pendik", label: "Pendik" },
  { value: "Sancaktepe", label: "Sancaktepe" },
  { value: "Sariyer", label: "Sarıyer" },
  { value: "Silivri", label: "Silivri" },
  { value: "Sultanbeyli", label: "Sultanbeyli" },
  { value: "Sultangazi", label: "Sultangazi" },
  { value: "Sile", label: "Şile" },
  { value: "Sisli", label: "Şişli" },
  { value: "Tuzla", label: "Tuzla" },
  { value: "Umraniye", label: "Ümraniye" },
  { value: "Uskudar", label: "Üsküdar" },
  { value: "Zeytinburnu", label: "Zeytinburnu" }
];

function CompareContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const districtsParam = searchParams.get("districts");
  
  // "Kadikoy,Besiktas" -> ["Kadikoy", "Besiktas"]
  const [selectedDistricts, setSelectedDistricts] = useState<string[]>([]);

  useEffect(() => {
    if (districtsParam) {
      setSelectedDistricts(districtsParam.split(",").filter(Boolean));
    }
  }, [districtsParam]);

  const { data, isLoading, error } = useAreaCompare(selectedDistricts);

  const updateUrl = (newDistricts: string[]) => {
    const params = new URLSearchParams(searchParams);
    if (newDistricts.length > 0) {
      params.set("districts", newDistricts.join(","));
    } else {
      params.delete("districts");
    }
    router.push(`/areas/compare?${params.toString()}`);
  };

  const addDistrict = (districtValue: string) => {
    if (selectedDistricts.includes(districtValue)) return;
    if (selectedDistricts.length >= 3) return; // Max 3 limit
    const newDistricts = [...selectedDistricts, districtValue];
    setSelectedDistricts(newDistricts);
    updateUrl(newDistricts);
  };

  const removeDistrict = (districtValue: string) => {
    const newDistricts = selectedDistricts.filter(d => d !== districtValue);
    setSelectedDistricts(newDistricts);
    updateUrl(newDistricts);
  };

  // Helper to highlight "winner" cells
  const getCellClass = (val: number, allVals: number[], type: 'high-good' | 'low-good') => {
    if (allVals.length < 2) return "";
    const max = Math.max(...allVals);
    const min = Math.min(...allVals);
    
    if (type === 'high-good') {
      return val === max ? "bg-emerald-50 text-emerald-700 font-semibold" : "";
    } else {
      return val === min ? "bg-emerald-50 text-emerald-700 font-semibold" : "";
    }
  };

  const formatCurrency = (val: number) => 
    new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(val);

  if (selectedDistricts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-[50vh] space-y-4">
        <div className="p-4 bg-gray-100 rounded-full">
          <BarChart3 className="w-8 h-8 text-gray-500" />
        </div>
        <h3 className="text-xl font-semibold">Karşılaştırma için ilçe seçin</h3>
        <div className="w-64">
           <Select
            options={ISTANBUL_DISTRICTS}
            onChange={(e) => addDistrict(e.target.value)}
            placeholder="İlçe ekle..."
          />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header & Controls */}
      <div className="bg-white p-6 rounded-xl border shadow-sm flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
           <div className="flex items-center gap-2 mb-1">
             <Link href="/areas" className="text-gray-400 hover:text-gray-600">
               <ArrowLeft className="w-5 h-5" />
             </Link>
             <h2 className="text-xl font-bold text-gray-900">Bölge Karşılaştırma</h2>
           </div>
           <p className="text-sm text-gray-500 ml-7">
             {selectedDistricts.length} bölge seçildi (Maksimum 3)
           </p>
        </div>

        <div className="flex flex-wrap gap-2 items-center">
          {selectedDistricts.map(d => {
            const label = ISTANBUL_DISTRICTS.find(opt => opt.value === d)?.label || d;
            return (
              <Badge key={d} variant="secondary" className="pl-3 pr-1 py-1.5 text-sm gap-2">
                {label}
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="h-4 w-4 rounded-full hover:bg-gray-200"
                  onClick={() => removeDistrict(d)}
                >
                  <X className="w-3 h-3" />
                </Button>
              </Badge>
            );
          })}
          
          {selectedDistricts.length < 3 && (
            <div className="w-[180px]">
              <Select
                options={ISTANBUL_DISTRICTS.filter(opt => !selectedDistricts.includes(opt.value))}
                onChange={(e) => addDistrict(e.target.value)}
                placeholder="Ekle..."
                className="h-9 border-dashed"
              />
            </div>
          )}
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
           {[1, 2, 3].map(i => <Skeleton key={i} className="h-64 w-full" />)}
        </div>
      ) : error ? (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Hata</AlertTitle>
          <AlertDescription>Veriler yüklenemedi.</AlertDescription>
        </Alert>
      ) : data?.areas ? (
        <>
          {/* Comparison Table */}
          <Card className="overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-gray-50 text-gray-600 uppercase text-xs font-semibold">
                  <tr>
                    <th className="px-6 py-4">Metrik</th>
                    {data.areas.map(area => {
                      const label = ISTANBUL_DISTRICTS.find(opt => opt.value === area.district)?.label || area.district;
                      return (
                        <th key={area.district} className="px-6 py-4">{label}</th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  <tr>
                    <td className="px-6 py-4 font-medium text-gray-900">Ortalama Satış (m²)</td>
                    {data.areas.map((area, _, arr) => (
                      <td key={area.district} className={cn("px-6 py-4", getCellClass(area.avg_price_sqm_sale, arr.map(a => a.avg_price_sqm_sale), 'low-good'))}>
                        {formatCurrency(area.avg_price_sqm_sale)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-6 py-4 font-medium text-gray-900">Ortalama Kira (m²)</td>
                    {data.areas.map((area, _, arr) => (
                      <td key={area.district} className={cn("px-6 py-4", getCellClass(area.avg_price_sqm_rent, arr.map(a => a.avg_price_sqm_rent), 'low-good'))}>
                        {formatCurrency(area.avg_price_sqm_rent)}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-6 py-4 font-medium text-gray-900">Yıllık Kira Verimi</td>
                    {data.areas.map((area, _, arr) => (
                      <td key={area.district} className={cn("px-6 py-4", getCellClass(area.investment_metrics?.kira_verimi ?? 0, arr.map(a => a.investment_metrics?.kira_verimi ?? 0), 'high-good'))}>
                        {area.investment_metrics?.kira_verimi ? `%${area.investment_metrics.kira_verimi.toFixed(2)}` : 'N/A'}
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-6 py-4 font-medium text-gray-900">Amortisman Süresi</td>
                    {data.areas.map((area, _, arr) => (
                      <td key={area.district} className={cn("px-6 py-4", getCellClass(area.investment_metrics?.amortisman_yil ?? 0, arr.map(a => a.investment_metrics?.amortisman_yil ?? 0), 'low-good'))}>
                        {area.investment_metrics?.amortisman_yil ?? 'N/A'} Yıl
                      </td>
                    ))}
                  </tr>
                  <tr>
                    <td className="px-6 py-4 font-medium text-gray-900">Yatırım Skoru</td>
                    {data.areas.map((area, _, arr) => (
                      <td key={area.district} className={cn("px-6 py-4", getCellClass(area.investment_score, arr.map(a => a.investment_score), 'high-good'))}>
                        <div className="flex items-center gap-2">
                          <span className="font-bold">{area.investment_score}</span>
                          <div className="h-1.5 w-16 bg-gray-200 rounded-full overflow-hidden">
                             <div className="h-full bg-blue-500" style={{ width: `${area.investment_score}%` }} />
                          </div>
                        </div>
                      </td>
                    ))}
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>

          {/* Bar Chart — Recharts lazy loaded */}
          <Card>
            <CardHeader>
              <CardTitle>Fiyat Karşılaştırması (Satış vs Kira)</CardTitle>
            </CardHeader>
            <CardContent className="h-[400px]">
              <CompareChart areas={data.areas} />
            </CardContent>
          </Card>
        </>
      ) : null}
    </div>
  );
}

export default function ComparePage() {
  return (
    <div className="p-6 max-w-[1600px] mx-auto min-h-screen bg-gray-50/50">
       <Suspense fallback={<Skeleton className="h-[400px] w-full" />}>
         <CompareContent />
       </Suspense>
    </div>
  );
}