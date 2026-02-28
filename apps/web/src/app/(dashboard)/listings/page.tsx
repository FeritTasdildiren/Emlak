"use client";

import { useState } from "react";
import dynamic from "next/dynamic";
import { useListingAssistant } from "@/hooks/use-listing-assistant";
import { ListingTextForm } from "./components/listing-text-form";
import { ListingTextResult } from "./components/listing-text-result";
import { FileText, Image as ImageIcon, Share2, Zap, Bell, Building2, Lock } from "lucide-react";
import { cn } from "@/lib/utils";
import { FeatureGate } from "@/components/feature-gate";
import { usePlan } from "@/hooks/use-plan";

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

export default function ListingsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('metin');
  const { isGenerating, result, generateText } = useListingAssistant();
  const { checkAccess } = usePlan();

  // Mock user credits
  const credits = 342;

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
            <div className="grid lg:grid-cols-2 gap-6 lg:gap-8 items-start animate-in fade-in slide-in-from-bottom-4 duration-500">
              <ListingTextForm 
                onSubmit={generateText} 
                isGenerating={isGenerating} 
              />
              <ListingTextResult 
                result={result?.data || null} 
                isLoading={isGenerating} 
                onRegenerate={() => {
                  console.log("Regenerate requested");
                }}
                onChangeTone={(tone) => {
                  console.log("Change tone to", tone);
                }}
              />
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
