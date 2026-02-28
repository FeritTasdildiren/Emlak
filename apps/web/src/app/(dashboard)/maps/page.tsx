"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import {
  X,
  Map as MapIcon,
  List,
  Search,
  Maximize2,
  AlertCircle
} from "lucide-react";
import type { Map } from 'maplibre-gl';
import { cn } from "@/lib/utils";

import { Button, buttonVariants } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";

import { AreaAnalysisCard } from "@/components/map/AreaAnalysisCard";
import { PropertyMarkerLayer, type Property } from "@/components/map/PropertyMarkerLayer";
import { EarthquakeRiskBadge } from "@/components/dashboard/earthquake-risk-badge";

import { useAreaAnalysis } from "@/hooks/use-area-analysis";
import { useDepremRisk } from "@/hooks/use-deprem-risk";
import { api } from "@/lib/api-client";

// GeoJSON API yanıt tipleri
interface GeoJSONFeatureProperties {
  id: string;
  title: string;
  price: number;
  listing_type: string;
  property_type: string;
  rooms: string;
  net_area: number;
  district: string;
}

interface GeoJSONFeature {
  type: "Feature";
  geometry: {
    type: "Point";
    coordinates: [number, number]; // [lon, lat]
  };
  properties: GeoJSONFeatureProperties;
}

interface GeoJSONResponse {
  type: "FeatureCollection";
  features: GeoJSONFeature[];
}

/** GeoJSON Feature → PropertyMarkerLayer Property dönüşümü */
function mapGeoJSONToProperties(data: GeoJSONResponse): Property[] {
  return data.features.map((f) => ({
    id: f.properties.id,
    lat: f.geometry.coordinates[1],
    lon: f.geometry.coordinates[0],
    price: f.properties.price,
    rooms: f.properties.rooms,
    sqm: f.properties.net_area,
    title: f.properties.title,
    district: f.properties.district,
  }));
}

// Harita bileşeni (SSR disabled)
const MapContainer = dynamic(() => import("@/components/map/MapContainer").then(mod => mod.MapContainer), {
  ssr: false,
  loading: () => (
    <div className="w-full h-screen bg-gray-100 flex items-center justify-center">
      <div className="flex flex-col items-center gap-2">
        <MapIcon className="w-10 h-10 text-gray-300 animate-pulse" />
        <span className="text-gray-400 font-medium">Harita yükleniyor...</span>
      </div>
    </div>
  )
});

// İlçe Koordinatları (Merkezler) — sidebar ilçe seçimi ve gelecekteki bbox filtreleme için
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const DISTRICT_COORDINATES: Record<string, [number, number]> = {
  "Kadıköy": [40.9811, 29.0620],
  "Beşiktaş": [41.0428, 29.0077],
  "Üsküdar": [41.0260, 29.0150],
  "Şişli": [41.0536, 28.9940],
  "Maltepe": [40.9248, 29.1306],
  "Ataşehir": [40.9933, 29.1130],
  "Sarıyer": [41.1663, 29.0498],
  "Fatih": [41.0082, 28.9784],
  "Bakırköy": [40.9801, 28.8721],
  "Beyoğlu": [41.0286, 28.9744],
  "Pendik": [40.8768, 29.2335],
  "Kartal": [40.8885, 29.1856],
  "Başakşehir": [41.0977, 28.8066]
};

export default function MapsPage() {
  const [selectedDistrict, setSelectedDistrict] = useState<string | null>(null);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  // Backend API'den harita property'lerini çek
  const {
    data: mapProperties = [],
    isLoading: isPropertiesLoading,
    isError: isPropertiesError,
  } = useQuery({
    queryKey: ["map-properties"],
    queryFn: async () => {
      const data = await api.get<GeoJSONResponse>(
        "/maps/properties?bbox=28.5,40.7,29.5,41.3&limit=200"
      );
      return mapGeoJSONToProperties(data);
    },
    staleTime: 2 * 60 * 1000,  // 2 dakika
    gcTime: 5 * 60 * 1000,     // 5 dakika
  });

  // Seçili bölge verileri
  const { data: areaData, isLoading: isAreaLoading } = useAreaAnalysis("Istanbul", selectedDistrict || "");
  const { data: riskData, isLoading: isRiskLoading } = useDepremRisk("Istanbul", selectedDistrict || "");

  const handleMarkerClick = (property: Property) => {
    setSelectedDistrict(property.district);
    if (!isSidebarOpen) setIsSidebarOpen(true);
  };

  const handleMapReady = (map: Map) => {
    // Harita yüklendiğinde yapılacaklar (örn: event listener)
    console.log("Map ready", map);
  };

  return (
    <div className="relative w-full h-[calc(100vh-64px)] overflow-hidden">
      {/* Harita */}
      <MapContainer
        className="w-full h-full z-0"
        center={[28.9784, 41.0082]} // İstanbul Merkez
        zoom={10}
        onMapReady={handleMapReady}
      >
        {!isPropertiesLoading && !isPropertiesError && (
          <PropertyMarkerLayer
            properties={mapProperties}
            onMarkerClick={handleMarkerClick}
          />
        )}
      </MapContainer>

      {/* Properties yükleniyor overlay */}
      {isPropertiesLoading && (
        <div className="absolute bottom-4 left-4 z-10 bg-white rounded-lg shadow-lg px-4 py-2 flex items-center gap-2">
          <div className="h-4 w-4 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
          <span className="text-sm text-gray-600">İlanlar yükleniyor...</span>
        </div>
      )}

      {/* Properties hata overlay */}
      {isPropertiesError && (
        <div className="absolute bottom-4 left-4 z-10 bg-red-50 border border-red-200 rounded-lg shadow-lg px-4 py-2 flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-red-500" />
          <span className="text-sm text-red-700">İlanlar yüklenemedi</span>
        </div>
      )}

      {/* Üst Arama Barı (Overlay) */}
      <div className="absolute top-4 left-4 right-4 md:w-96 z-10">
        <div className="bg-white rounded-lg shadow-lg p-2 flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
            <Input 
              placeholder="Bölge veya ilan ara..." 
              className="pl-9 border-0 bg-gray-50 focus-visible:ring-0"
            />
          </div>
          <Button variant="ghost" size="icon" onClick={() => setIsSidebarOpen(!isSidebarOpen)}>
            <List className="h-5 w-5" />
          </Button>
        </div>
      </div>

      {/* Yan Panel (Desktop only — mobilde bottom sheet kullanılır) */}
      <div
        className={`
          hidden md:block absolute top-0 right-0 h-full md:w-[400px] bg-white shadow-2xl z-20
          transform transition-transform duration-300 ease-in-out border-l
          ${selectedDistrict && isSidebarOpen ? 'md:translate-x-0' : 'translate-x-full'}
        `}
      >
        <div className="flex flex-col h-full">
          {/* Header */}
          <div className="p-4 border-b flex justify-between items-center bg-gray-50">
            <div>
              <h2 className="font-bold text-lg text-gray-900">{selectedDistrict || "Bölge Detayı"}</h2>
              <p className="text-xs text-gray-500">İstanbul</p>
            </div>
            <Button variant="ghost" size="icon" onClick={() => setSelectedDistrict(null)}>
              <X className="h-5 w-5" />
            </Button>
          </div>

          {/* Content */}
          <ScrollArea className="flex-1 p-4">
            <div className="space-y-6">
              {selectedDistrict ? (
                <>
                  {/* Deprem Riski Badge */}
                  <div className="flex items-center justify-between bg-white p-3 rounded-lg border shadow-sm">
                    <span className="text-sm font-medium text-gray-700">Deprem Riski</span>
                    {isRiskLoading ? (
                      <Skeleton className="h-8 w-24 rounded-full" />
                    ) : riskData ? (
                      <EarthquakeRiskBadge 
                        score={riskData.risk_score} 
                        riskLevel={(riskData.risk_score || 0) > 7 ? 'high' : (riskData.risk_score || 0) > 4 ? 'medium' : 'low'}
                        showLabel 
                      />
                    ) : null}
                  </div>

                  {/* Bölge Analizi */}
                  {isAreaLoading ? (
                    <Skeleton className="h-[300px] w-full rounded-xl" />
                  ) : areaData ? (
                    <AreaAnalysisCard
                      regionName={selectedDistrict}
                      demographics={{
                        population: areaData.population || 0,
                        density: "N/A"
                      }}
                      pricing={{
                        avgSalePrice: areaData.avg_price_sqm_sale || 0,
                        avgRentPrice: areaData.avg_price_sqm_rent,
                        changePercentage: areaData.price_trend_6m
                      }}
                      investment={{
                        roi: areaData.investment_score, 
                        amortizationYears: areaData.amortization_years,
                        score: areaData.investment_score
                      }}
                      risk={{
                        level: (riskData?.risk_score || 0) > 7 ? 'high' : (riskData?.risk_score || 0) > 4 ? 'medium' : 'low',
                        pgaValue: riskData?.pga_value,
                        groundClass: riskData?.soil_class
                      }}
                    />
                  ) : (
                    <div className="text-center py-10 text-gray-500">Bölge verisi bulunamadı.</div>
                  )}

                  <a
                    href={`/areas?district=${selectedDistrict}`}
                    className={cn(buttonVariants({ variant: "outline" }), "w-full")}
                  >
                    <Maximize2 className="w-4 h-4 mr-2" />
                    Detaylı Raporu Gör
                  </a>
                </>
              ) : (
                <div className="flex flex-col items-center justify-center h-[50vh] text-center text-gray-500">
                  <MapIcon className="w-12 h-12 mb-4 opacity-20" />
                  <p>Harita üzerinden bir mülk veya bölge seçerek detayları görüntüleyebilirsiniz.</p>
                </div>
              )}
            </div>
          </ScrollArea>
        </div>
      </div>

      {/* Mobil Bottom Sheet (Basitleştirilmiş) */}
      <div 
        className={`
          md:hidden absolute bottom-0 left-0 right-0 bg-white rounded-t-2xl shadow-[0_-5px_20px_rgba(0,0,0,0.1)] z-30
          transition-transform duration-300 ease-in-out
          ${selectedDistrict ? 'translate-y-0' : 'translate-y-full'}
        `}
      >
        <div className="p-2 flex justify-center">
          <div className="w-12 h-1.5 bg-gray-300 rounded-full" />
        </div>
        <div className="p-4 pt-2">
          <div className="flex justify-between items-center mb-4">
             <h3 className="font-bold text-lg">{selectedDistrict}</h3>
             <Button variant="ghost" size="icon" onClick={() => setSelectedDistrict(null)}>
               <X className="h-5 w-5" />
             </Button>
          </div>
          {areaData && (
             <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-gray-50 p-3 rounded-lg">
                   <p className="text-xs text-gray-500">Ort. m²</p>
                   <p className="font-semibold">{new Intl.NumberFormat('tr-TR', { style: 'currency', currency: 'TRY', maximumFractionDigits: 0 }).format(areaData.avg_price_sqm_sale || 0)}</p>
                </div>
                <div className="bg-gray-50 p-3 rounded-lg">
                   <p className="text-xs text-gray-500">Yatırım Skoru</p>
                   <p className="font-semibold">{areaData.investment_score || '-'}/100</p>
                </div>
             </div>
          )}
          <a
            href={`/areas?district=${selectedDistrict}`}
            className={cn(buttonVariants({ variant: "default" }), "w-full")}
          >
            Detayları Gör
          </a>
        </div>
      </div>
    </div>
  );
}
