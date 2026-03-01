"use client";

import { useRef, useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { useListingAssistant } from "@/hooks/use-listing-assistant";
import { ListingTextForm } from "./components/listing-text-form";
import { ListingTextResult } from "./components/listing-text-result";
import { FileText, Image as ImageIcon, Share2, Zap, Bell, Building2, Lock, AlertCircle, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { FeatureGate } from "@/components/feature-gate";
import { usePlan } from "@/hooks/use-plan";
import type { ListingFormData, ToneType } from "@/types/listing";
import { api } from "@/lib/api-client";
import type { Property } from "@/types/property";

// Tab bileşenlerini lazy load — kullanıcı tab'a tıklayana kadar yüklenmez
const VirtualStagingTab = dynamic(
  () => import("./components/virtual-staging-tab").then(mod => ({ default: mod.VirtualStagingTab })),
  { loading: () => <div className="h-64 w-full animate-pulse bg-slate-100 dark:bg-slate-800 rounded-lg" /> }
);
const PortalExportTab = dynamic(
  () => import("./components/portal-export-tab").then(mod => ({ default: mod.PortalExportTab })),
  { loading: () => <div className="h-64 w-full animate-pulse bg-slate-100 dark:bg-slate-800 rounded-lg" /> }
);

type TabType = 'metin' | 'staging' | 'export';

function ListingsPageContent() {
  const searchParams = useSearchParams();
  const propertyId = searchParams.get("property_id");
  const [activeTab, setActiveTab] = useState<TabType>('metin');
  const { isGenerating, result, error, generateText, regenerateText } = useListingAssistant();
  const { checkAccess } = usePlan();
  const lastFormDataRef = useRef<ListingFormData | null>(null);
  const [prefillData, setPrefillData] = useState<Partial<ListingFormData> | null>(null);
  const [selectedProperty, setSelectedProperty] = useState<Property | null>(null);

  // Mock user credits
  const credits = 342;

  // property_id varsa veriyi çek
  useEffect(() => {
    if (propertyId) {
      api.get<Property>(`/properties/${propertyId}`)
        .then((property) => {
          setSelectedProperty(property);
          // Mapping: Property -> ListingFormData
          const mappedData: Partial<ListingFormData> = {
            propertyType: property.property_type as ListingFormData['propertyType'],
            price: property.price,
            city: property.city,
            district: property.district,
            neighborhood: property.neighborhood || undefined,
            grossSqm: property.area_sqm,
            netSqm: property.area_sqm, // Eger net yoksa brutu kullan
            roomCount: (property.room_count as ListingFormData['roomCount']) || undefined,
            bathroomCount: (property.bathroom_count?.toString() as ListingFormData['bathroomCount']) || undefined,
            floor: property.floor || undefined,
            totalFloors: property.total_floors || undefined,
            buildingAge: property.building_age || undefined,
            heatingType: property.heating_type as ListingFormData['heatingType'] || undefined,
            furnitureStatus: property.furniture_status as ListingFormData['furnitureStatus'] || undefined,
            facade: property.facade as ListingFormData['facade'] || undefined,
          };
          setPrefillData(mappedData);
        })
        .catch((err) => {
          console.error("Mülk bilgileri alınamadı:", err);
        });
    }
  }, [propertyId]);

  /** Form submit — formu kaydet + metin üret */
  const handleGenerate = (data: ListingFormData) => {
    lastFormDataRef.current = data;
    // property_id'yi de ekle (opsiyonel ister)
    const dataWithId = propertyId ? { ...data, property_id: propertyId } : data;
    generateText(dataWithId as ListingFormData);
  };

  /** Yeniden üret — aynı form datası ile regenerate endpoint çağır */
  const handleRegenerate = () => {
    if (lastFormDataRef.current) {
      regenerateText(lastFormDataRef.current);
    }
  };

  /** Ton değiştir — form datasındaki tonu güncelle + regenerate */
  const handleChangeTone = (tone: ToneType) => {
    if (lastFormDataRef.current) {
      lastFormDataRef.current = { ...lastFormDataRef.current, tone };
      regenerateText(lastFormDataRef.current);
    }
  };

  return (
    <div className="h-full flex flex-col bg-slate-50 text-slate-900 dark:bg-slate-950 dark:text-slate-100 min-h-screen">
      
      {/* HEADER */}
      <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 px-4 sm:px-6 py-4 flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-indigo-100 dark:bg-indigo-900/50 rounded-lg text-indigo-600 dark:text-indigo-400">
            <Building2 className="w-6 h-6" />
          </div>
          <h1 className="text-xl font-bold text-slate-800 dark:text-slate-100">İlan Asistanı</h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-400 rounded-full text-sm font-medium border border-emerald-100 dark:border-emerald-800">
            <Zap className="w-4 h-4" />
            <span>{credits} Kredi</span>
          </div>
          <button className="p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full transition-colors" aria-label="Bildirimler">
            <Bell className="w-5 h-5" />
          </button>
          <div className="w-8 h-8 bg-indigo-600 rounded-full text-white flex items-center justify-center font-bold text-sm">F</div>
        </div>
      </header>

      {/* MAIN CONTENT */}
      <main className="flex-1 max-w-7xl mx-auto w-full p-4 sm:p-6 lg:p-8">
        
        {/* TABS */}
        <div className="mb-6 sm:mb-8 border-b border-slate-200 dark:border-slate-800 overflow-x-auto">
          <nav className="flex gap-6 sm:gap-8 -mb-px min-w-max">
            <button
              onClick={() => setActiveTab('metin')}
              className={cn(
                "py-4 px-1 inline-flex items-center gap-2 font-medium text-sm whitespace-nowrap border-b-2 transition-colors",
                activeTab === 'metin'
                  ? "border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400"
                  : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:border-slate-300"
              )}
            >
              <FileText className="w-4 h-4" />
              Metin Oluştur
              {!checkAccess('hasAiAssistant') && <Lock className="w-3 h-3 text-amber-500" />}
            </button>
            <button
              onClick={() => setActiveTab('staging')}
              className={cn(
                "py-4 px-1 inline-flex items-center gap-2 font-medium text-sm whitespace-nowrap border-b-2 transition-colors",
                activeTab === 'staging'
                  ? "border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400"
                  : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:border-slate-300"
              )}
            >
              <ImageIcon className="w-4 h-4" />
              Virtual Staging
              {!checkAccess('hasVirtualStaging') && <Lock className="w-3 h-3 text-amber-500" />}
              <span className="bg-indigo-100 dark:bg-indigo-900/50 text-indigo-700 dark:text-indigo-300 py-0.5 px-2 rounded-full text-xs font-semibold">YENİ</span>
            </button>
            <button
              onClick={() => setActiveTab('export')}
              className={cn(
                "py-4 px-1 inline-flex items-center gap-2 font-medium text-sm whitespace-nowrap border-b-2 transition-colors",
                activeTab === 'export'
                  ? "border-indigo-600 text-indigo-600 dark:text-indigo-400 dark:border-indigo-400"
                  : "border-transparent text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 hover:border-slate-300"
              )}
            >
              <Share2 className="w-4 h-4" />
              Portal Export
              {!checkAccess('hasPortalExport') && <Lock className="w-3 h-3 text-amber-500" />}
            </button>
          </nav>
        </div>

        {/* TAB CONTENT */}
        {activeTab === 'metin' && (
          <FeatureGate feature="hasAiAssistant" featureName="İlan Metni Oluşturma" requiredPlan="pro">
            <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
              {error && (
                <div className="flex items-start gap-3 p-4 rounded-lg border border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-900/20 text-sm text-red-700 dark:text-red-300">
                  <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                  <p>{error}</p>
                </div>
              )}

              {selectedProperty && (
                <div className="flex items-center gap-3 p-4 rounded-lg border border-indigo-100 bg-indigo-50 dark:border-indigo-900/30 dark:bg-indigo-900/10 text-sm text-indigo-700 dark:text-indigo-300">
                  <Info className="w-5 h-5 shrink-0" />
                  <p>
                    <span className="font-semibold">{selectedProperty.title}</span> ilanı için metin oluşturuyorsunuz.
                  </p>
                </div>
              )}

              <div className="grid lg:grid-cols-2 gap-6 lg:gap-8 items-start">
                <ListingTextForm
                  onSubmit={handleGenerate}
                  isGenerating={isGenerating}
                  initialData={prefillData || undefined}
                />
                <ListingTextResult
                  result={result?.data || null}
                  isLoading={isGenerating}
                  onRegenerate={handleRegenerate}
                  onChangeTone={handleChangeTone}
                />
              </div>
            </div>
          </FeatureGate>
        )}

        {activeTab === 'staging' && (
           <FeatureGate feature="hasVirtualStaging" featureName="Virtual Staging" requiredPlan="elite">
             <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <VirtualStagingTab />
             </div>
           </FeatureGate>
        )}

        {activeTab === 'export' && (
           <FeatureGate feature="hasPortalExport" featureName="Portal Export" requiredPlan="pro">
             <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
                <PortalExportTab generatedText={result?.data || null} />
             </div>
           </FeatureGate>
        )}

      </main>
    </div>
  );
}

export default function ListingsPage() {
  return (
    <Suspense fallback={<div className="h-full w-full flex items-center justify-center min-h-[400px]">Yükleniyor...</div>}>
      <ListingsPageContent />
    </Suspense>
  );
}
