"use client";

import { Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  BarChart3,
  MapPin,
  AlertCircle,
  Building2,
  TrendingUp
} from "lucide-react";

import { AreaAnalysisCard } from "@/components/map/AreaAnalysisCard";
import { EarthquakeRiskCard } from "@/components/dashboard/earthquake-risk-card";
import { cities, getDistrictsForCity } from "@/lib/location-data";

// Recharts ağır kütüphane — lazy load ile bundle'dan ayır
const PriceTrendChart = dynamic(
  () => import("@/components/dashboard/price-trend-chart").then(mod => ({ default: mod.PriceTrendChart })),
  { loading: () => <div className="h-[300px] w-full animate-pulse bg-gray-100 rounded-lg" /> }
);
import { Select } from "@/components/ui/select";
import { Button, buttonVariants } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";

import { useAreaAnalysis } from "@/hooks/use-area-analysis";
import { useDepremRisk } from "@/hooks/use-deprem-risk";
import { useAreaTrends } from "@/hooks/use-area-trends";

// Şehir value → label mapping
const cityLabelMap: Record<string, string> = {
  istanbul: "İstanbul",
  ankara: "Ankara",
  izmir: "İzmir",
};

function AreaContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const district = searchParams.get("district");
  const cityParam = searchParams.get("city") || "istanbul";
  const city = cityLabelMap[cityParam] || "İstanbul";

  // Seçili şehre göre ilçe listesi
  const districts = getDistrictsForCity(cityParam);

  const handleCityChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    const params = new URLSearchParams();
    params.set("city", value);
    // Şehir değiştiğinde ilçe seçimini sıfırla
    router.push(`/areas?${params.toString()}`);
  };

  const handleDistrictChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value;
    const params = new URLSearchParams(searchParams);
    params.set("city", cityParam);
    params.set("district", value);
    router.push(`/areas?${params.toString()}`);
  };

  // Hooks
  const { 
    data: areaData, 
    isLoading: isAreaLoading, 
    error: areaError 
  } = useAreaAnalysis(city, district || "");

  const { 
    data: riskData, 
    isLoading: isRiskLoading 
  } = useDepremRisk(city, district || "");

  const { 
    data: trendData, 
    isLoading: isTrendLoading 
  } = useAreaTrends(city, district || "", 12);

  if (!district) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center space-y-6">
        <div className="bg-blue-50 p-6 rounded-full">
          <MapPin className="w-12 h-12 text-blue-600" />
        </div>
        <div className="space-y-2 max-w-md">
          <h2 className="text-2xl font-bold text-gray-900">Bir Bölge Seçin</h2>
          <p className="text-gray-500">
            Detaylı pazar analizi, fiyat trendleri ve risk raporlarını görüntülemek için lütfen listeden bir il ve ilçe seçin.
          </p>
        </div>
        <div className="w-full max-w-xs space-y-3">
          <Select
            options={cities}
            value={cityParam}
            onChange={handleCityChange}
            placeholder="İl seçiniz..."
          />
          <Select
            options={districts}
            onChange={handleDistrictChange}
            placeholder="İlçe seçiniz..."
          />
        </div>
      </div>
    );
  }

  if (areaError) {
    return (
      <Alert variant="destructive" className="mt-6">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Hata</AlertTitle>
        <AlertDescription>
          Bölge verileri yüklenirken bir sorun oluştu. Lütfen daha sonra tekrar deneyiniz.
        </AlertDescription>
      </Alert>
    );
  }

  // Find label for current district
  const districtLabel = districts.find(d => d.value === district)?.label || district;

  return (
    <div className="space-y-6 animate-in fade-in duration-500">
      {/* Üst Bar: Seçim ve Aksiyonlar */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white p-4 rounded-lg border shadow-sm">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-100 rounded-lg">
            <Building2 className="w-5 h-5 text-blue-600" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-gray-900">{districtLabel}, {city}</h2>
            <p className="text-xs text-gray-500">Pazar Analizi Raporu</p>
          </div>
        </div>
        
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <div className="w-[140px]">
            <Select
              options={cities}
              value={cityParam}
              onChange={handleCityChange}
            />
          </div>
          <div className="w-[180px]">
            <Select
              options={districts}
              value={district}
              onChange={handleDistrictChange}
            />
          </div>
          
          <Link 
            href={`/areas/compare?districts=${district}`}
            className={cn(buttonVariants({ variant: "outline" }))}
          >
            <BarChart3 className="w-4 h-4 mr-2" />
            Karşılaştır
          </Link>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Sol Kolon: Ana Analiz Kartı (2 birim genişlik) */}
        <div className="lg:col-span-2 space-y-6">
          {isAreaLoading ? (
            <Skeleton className="h-[300px] w-full rounded-xl" />
          ) : areaData ? (
            <AreaAnalysisCard
              regionName={`${districtLabel} Genel Bakış`}
              demographics={{
                population: areaData.population || 0,
                density: "Yüksek" // API'den gelmiyorsa placeholder
              }}
              pricing={{
                avgSalePrice: areaData.avg_price_sqm_sale || 0,
                avgRentPrice: areaData.avg_price_sqm_rent,
                changePercentage: areaData.price_trend_6m
              }}
              investment={{
                roi: areaData.investment_score ? areaData.investment_score * 1.5 : undefined, // Mock calculation
                amortizationYears: areaData.amortization_years,
                score: areaData.investment_score
              }}
              risk={{
                level: (riskData?.risk_score || 0) > 7 ? 'high' : (riskData?.risk_score || 0) > 4 ? 'medium' : 'low',
                pgaValue: riskData?.pga_value,
                groundClass: riskData?.soil_class
              }}
              className="h-full"
            />
          ) : null}

          {/* Fiyat Trend Grafiği */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base font-semibold flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-blue-600" />
                Fiyat Trend Analizi (Son 12 Ay)
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isTrendLoading ? (
                <Skeleton className="h-[300px] w-full" />
              ) : trendData ? (
                <PriceTrendChart
                  trends={trendData.trends.map(t => ({
                    month: t.month,
                    avgPriceSqm: t.price_sqm_sale,
                    sampleCount: undefined
                  }))}
                  changePct={trendData.change_pct_sale}
                  type="sale"
                  height={300}
                />
              ) : (
                <div className="h-[300px] flex items-center justify-center text-gray-400 border border-dashed rounded-lg">
                  Trend verisi bulunamadı
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sağ Kolon: Risk ve Diğer Detaylar (1 birim genişlik) */}
        <div className="space-y-6">
          {isRiskLoading ? (
            <Skeleton className="h-[400px] w-full rounded-xl" />
          ) : riskData ? (
            <EarthquakeRiskCard
              score={riskData.risk_score}
              riskLevel={(riskData.risk_score || 0) > 7 ? 'high' : (riskData.risk_score || 0) > 4 ? 'medium' : 'low'}
              faultDistanceKm={riskData.fault_distance_km}
              soilClass={riskData.soil_class}
              pgaValue={riskData.pga_value}
              showDisclaimer={true}
            />
          ) : null}

          {/* Ek Bilgi Kartı (Placeholder) */}
          <Card className="bg-gradient-to-br from-indigo-50 to-blue-50 border-blue-100">
            <CardContent className="p-6">
              <h3 className="font-semibold text-indigo-900 mb-2">Yatırım Fırsatı</h3>
              <p className="text-sm text-indigo-700 mb-4">
                Bu bölgedeki amortisman süreleri son 6 ayda %5 oranında iyileşme gösterdi.
              </p>
              <Button size="sm" className="w-full bg-indigo-600 hover:bg-indigo-700 text-white">
                Raporu İndir
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function AreasPage() {
  return (
    <div className="p-6 max-w-[1600px] mx-auto min-h-screen bg-gray-50/50">
      <div className="mb-8">
        <h1 className="text-3xl font-bold tracking-tight text-gray-900">Bölge Analizi</h1>
        <p className="text-gray-500 mt-2">
          İlçe bazlı detaylı pazar verileri, demografik yapı ve risk analizleri.
        </p>
      </div>

      <Suspense fallback={<Skeleton className="h-[400px] w-full" />}>
        <AreaContent />
      </Suspense>
    </div>
  );
}