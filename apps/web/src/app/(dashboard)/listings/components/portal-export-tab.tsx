"use client";

import { useState } from "react";
import { GeneratedListing, PortalType } from "@/types/listing";
import { Button } from "@/components/ui/button";
import { Share2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { toast } from "@/components/ui/toast";

interface PortalExportTabProps {
  generatedText: GeneratedListing | null;
}

export function PortalExportTab({ generatedText }: PortalExportTabProps) {
  const [selectedPortal, setSelectedPortal] = useState<PortalType>('both');
  const [isExporting, setIsExporting] = useState(false);

  const handleExport = async () => {
    setIsExporting(true);
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500));
    setIsExporting(false);
    // In real app, this would trigger download or open link
    toast("İlan portallara aktarılmak üzere hazırlandı!");
  };

  if (!generatedText) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden min-h-[500px] flex flex-col items-center justify-center p-8 text-center">
        <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
          <Share2 className="w-8 h-8 text-slate-400 dark:text-slate-500" />
        </div>
        <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300">Önce İlan Metni Oluşturun</h3>
        <p className="mt-1 text-xs text-slate-400 dark:text-slate-500 max-w-xs">
          Portal entegrasyonu yapabilmek için önce &apos;Metin Oluştur&apos; sekmesinden bir ilan oluşturmalısınız.
        </p>
      </div>
    );
  }

  return (
    <div className="grid lg:grid-cols-12 gap-6 lg:gap-8 items-start">
      {/* Left: Settings */}
      <div className="lg:col-span-4 space-y-6">
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5 sm:p-6">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200 mb-4">Portal Seçimi</h3>
          
          <div className="space-y-3">
             {[ 
                { id: 'sahibinden', label: 'Sahibinden.com', color: 'bg-yellow-400' },
                { id: 'hepsiemlak', label: 'Hepsiemlak', color: 'bg-red-500' },
                { id: 'both', label: 'Her İkisi (Otomatik Format)', color: 'bg-indigo-500' }
             ].map((portal) => (
                <label key={portal.id} className="flex items-center gap-3 p-3 border border-slate-200 dark:border-slate-700 rounded-lg cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors">
                   <input 
                      type="radio" 
                      name="portal" 
                      value={portal.id} 
                      checked={selectedPortal === portal.id}
                      onChange={() => setSelectedPortal(portal.id as PortalType)}
                      className="w-4 h-4 text-indigo-600 focus:ring-indigo-500 border-slate-300"
                   />
                   <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-xs", portal.color)}>
                      {portal.label.substring(0, 1)}
                   </div>
                   <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{portal.label}</span>
                </label>
             ))}
          </div>

          <div className="mt-6 pt-6 border-t border-slate-100 dark:border-slate-800">
             <Button 
               onClick={handleExport}
               disabled={isExporting}
               className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-6"
             >
                {isExporting ? (
                   <span className="flex items-center gap-2">
                      <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
                      Hazırlanıyor...
                   </span>
                ) : (
                   <span className="flex items-center gap-2">
                      <Share2 className="w-5 h-5" />
                      Portala Aktar
                   </span>
                )}
             </Button>
             <p className="mt-2 text-center text-xs text-slate-400 dark:text-slate-500">Otomatik format düzenlemesi yapılır</p>
          </div>
        </div>
      </div>

      {/* Right: Preview */}
      <div className="lg:col-span-8 space-y-6">
         <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden flex flex-col">
            <div className="bg-slate-50 dark:bg-slate-800/50 px-5 sm:px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center">
               <h3 className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2 text-sm">
                  Portal Önizleme
               </h3>
               <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-500 dark:text-slate-400">
                     {selectedPortal === 'sahibinden' ? 'Sahibinden.com Formatı' : 
                      selectedPortal === 'hepsiemlak' ? 'Hepsiemlak Formatı' : 'Evrensel Format'}
                  </span>
               </div>
            </div>

            <div className="p-6 overflow-y-auto max-h-[600px] bg-white dark:bg-slate-950">
               <div className="max-w-3xl mx-auto border border-slate-200 dark:border-slate-800 rounded-lg p-8 shadow-sm">
                  <h1 className="text-xl font-bold text-slate-900 dark:text-slate-100 mb-4 pb-4 border-b border-slate-100 dark:border-slate-800">
                     {generatedText.title}
                  </h1>
                  <div className="prose prose-sm dark:prose-invert max-w-none space-y-4">
                     {generatedText.description.split('\n').map((para, i) => (
                        <p key={i}>{para}</p>
                     ))}
                  </div>
                  
                  {generatedText.highlights && (
                     <div className="mt-8 p-4 bg-slate-50 dark:bg-slate-900 rounded-lg">
                        <h4 className="font-semibold text-slate-900 dark:text-slate-200 mb-2">Öne Çıkan Özellikler</h4>
                        <ul className="list-disc pl-5 space-y-1 text-sm text-slate-600 dark:text-slate-400">
                           {generatedText.highlights.map((h, i) => <li key={i}>{h}</li>)}
                        </ul>
                     </div>
                  )}
               </div>
            </div>
         </div>
      </div>
    </div>
  );
}
