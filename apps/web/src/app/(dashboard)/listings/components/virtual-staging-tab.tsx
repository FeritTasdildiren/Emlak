"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useVirtualStaging } from "@/hooks/use-virtual-staging";
import { StagingStyle } from "@/types/listing";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { 
  UploadCloud, 
  Check, 
  Minus, 
  Crown, 
  Square, 
  Trees, 
  Flower2, 
  Wrench, 
  Wand2, 
  Image as ImageIcon,
  EyeOff,
  Sparkles,
  ChevronsLeftRight,
  RefreshCw,
  Download
} from "lucide-react";


export function VirtualStagingTab() {
  const { isProcessing, result, styles, stageImage } = useVirtualStaging();
  const [selectedStyle, setSelectedStyle] = useState<StagingStyle>('modern');
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [sliderPosition, setSliderPosition] = useState(50);
  const [isDragging, setIsDragging] = useState(false);
  const sliderRef = useRef<HTMLDivElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setUploadedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setUploadedFile(file);
      const url = URL.createObjectURL(file);
      setPreviewUrl(url);
    }
  };

  const handleStage = async () => {
    if (!uploadedFile) return;
    await stageImage({
      imageFile: uploadedFile,
      style: selectedStyle
    });
  };

  const handleMove = useCallback((clientX: number) => {
    if (sliderRef.current) {
      const rect = sliderRef.current.getBoundingClientRect();
      const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
      const percentage = (x / rect.width) * 100;
      setSliderPosition(percentage);
    }
  }, []);

  const onMouseDown = () => setIsDragging(true);
  const onMouseUp = () => setIsDragging(false);
  const onMouseMove = (e: React.MouseEvent) => {
    if (isDragging) handleMove(e.clientX);
  };
  
  const onTouchStart = () => setIsDragging(true);
  const onTouchEnd = () => setIsDragging(false);
  const onTouchMove = (e: React.TouchEvent) => {
     if (isDragging) handleMove(e.touches[0].clientX);
  };

  useEffect(() => {
    if (isDragging) {
      window.addEventListener('mouseup', onMouseUp);
      window.addEventListener('touchend', onTouchEnd);
    } else {
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('touchend', onTouchEnd);
    }
    return () => {
      window.removeEventListener('mouseup', onMouseUp);
      window.removeEventListener('touchend', onTouchEnd);
    };
  }, [isDragging]);


  const getStyleIcon = (id: string) => {
    switch (id) {
      case 'modern': return <Minus className="w-5 h-5" />;
      case 'klasik': return <Crown className="w-5 h-5" />;
      case 'minimalist': return <Square className="w-5 h-5" />;
      case 'skandinav': return <Trees className="w-5 h-5" />;
      case 'bohem': return <Flower2 className="w-5 h-5" />;
      case 'endustriyel': return <Wrench className="w-5 h-5" />;
      default: return <Minus className="w-5 h-5" />;
    }
  };

  return (
    <div className="grid lg:grid-cols-12 gap-6 lg:gap-8 items-start">
      {/* LEFT COLUMN: CONTROLS */}
      <div className="lg:col-span-4 space-y-6">
        
        {/* 1. Upload */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5 sm:p-6">
          <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200 mb-4 flex items-center gap-2">
            <span className="w-6 h-6 bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 rounded-full flex items-center justify-center text-xs font-bold">1</span>
            Fotoğraf Yükle
          </h3>

          <div 
            className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg p-6 sm:p-8 text-center hover:border-indigo-500 dark:hover:border-indigo-400 hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-all cursor-pointer group relative"
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
          >
            <input 
              type="file" 
              accept="image/*" 
              onChange={handleFileChange} 
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />
            <div className="w-12 h-12 bg-indigo-50 dark:bg-indigo-900/40 text-indigo-600 dark:text-indigo-400 rounded-full flex items-center justify-center mx-auto mb-3 group-hover:scale-110 transition-transform">
              <UploadCloud className="w-6 h-6" />
            </div>
            <p className="text-sm font-medium text-slate-700 dark:text-slate-300">Tıkla veya sürükle</p>
            <p className="text-xs text-slate-400 dark:text-slate-500 mt-1">JPG, PNG, WebP (Maks. 10MB)</p>
          </div>

          {previewUrl && (
             <div className="mt-4 relative group rounded-lg overflow-hidden aspect-square border-2 border-emerald-500 dark:border-emerald-400 max-w-[100px]">
                <img src={previewUrl} alt="Preview" className="w-full h-full object-cover" />
                <div className="absolute top-1 right-1 w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center">
                    <Check className="w-3 h-3 text-white" />
                </div>
             </div>
          )}
        </div>

        {/* 2. Style Selection */}
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm p-5 sm:p-6">
           <h3 className="text-sm font-semibold text-slate-900 dark:text-slate-200 mb-4 flex items-center gap-2">
            <span className="w-6 h-6 bg-indigo-100 dark:bg-indigo-900/50 text-indigo-600 dark:text-indigo-400 rounded-full flex items-center justify-center text-xs font-bold">2</span>
            Tarz Seç
          </h3>
          <div className="grid grid-cols-2 gap-3">
             {styles.map((style) => (
                <label key={style.id} className="cursor-pointer">
                   <input 
                      type="radio" 
                      name="stagingStyle" 
                      value={style.id} 
                      checked={selectedStyle === style.id}
                      onChange={() => setSelectedStyle(style.id)}
                      className="peer sr-only"
                   />
                   <div className={cn(
                      "p-3 rounded-lg border-2 transition-all text-center h-full",
                      selectedStyle === style.id 
                         ? "border-indigo-600 dark:border-indigo-400 bg-indigo-50 dark:bg-indigo-900/30 shadow-md"
                         : "border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800"
                   )}>
                      <div className={cn(
                         "w-10 h-10 mx-auto mb-2 rounded-lg flex items-center justify-center",
                         selectedStyle === style.id
                            ? "bg-white dark:bg-slate-800 text-indigo-600"
                            : "bg-slate-100 dark:bg-slate-800 text-slate-500 dark:text-slate-400"
                      )}>
                         {getStyleIcon(style.id)}
                      </div>
                      <p className="text-sm font-medium text-slate-700 dark:text-slate-300">{style.label}</p>
                   </div>
                </label>
             ))}
          </div>
        </div>

        {/* Quota */}
        <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-xl p-4 border border-indigo-100 dark:border-indigo-800/50">
             <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-indigo-900 dark:text-indigo-200">Staging Kotası</span>
                <span className="text-sm font-bold text-indigo-700 dark:text-indigo-300">12 / 50</span>
             </div>
             <div className="w-full bg-indigo-200 dark:bg-indigo-800 rounded-full h-2.5">
                <div className="bg-indigo-600 dark:bg-indigo-400 h-2.5 rounded-full transition-all" style={{ width: '24%' }}></div>
             </div>
             <p className="mt-1.5 text-xs text-indigo-600 dark:text-indigo-400">Bu ay 38 staging hakkınız kaldı</p>
        </div>

        <Button
          onClick={handleStage}
          disabled={!uploadedFile || isProcessing}
          className="w-full bg-indigo-600 hover:bg-indigo-700 text-white py-6"
        >
           {isProcessing ? (
               <span className="flex items-center gap-2">
                   <span className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></span>
                   Dönüştürülüyor...
               </span>
           ) : (
               <span className="flex items-center gap-2">
                   <Wand2 className="w-5 h-5" />
                   Fotoğrafı Dönüştür
               </span>
           )}
        </Button>
      </div>

      {/* RIGHT COLUMN: PREVIEW */}
      <div className="lg:col-span-8">
         {isProcessing ? (
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden min-h-[520px] flex flex-col items-center justify-center p-8">
               <div className="relative">
                  <div className="w-20 h-20 border-4 border-indigo-200 dark:border-indigo-800 rounded-full animate-spin border-t-indigo-600 dark:border-t-indigo-400"></div>
                  <div className="absolute inset-0 flex items-center justify-center">
                     <ImageIcon className="w-8 h-8 text-indigo-600 dark:text-indigo-400" />
                  </div>
               </div>
               <p className="mt-6 text-sm font-medium text-slate-700 dark:text-slate-300">Fotoğraf işleniyor...</p>
               <p className="mt-1 text-xs text-slate-400 dark:text-slate-500">AI mobilya yerleştirmesi yapılıyor</p>
            </div>
         ) : result ? (
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden flex flex-col">
               {/* Header */}
               <div className="bg-slate-50 dark:bg-slate-800/50 px-5 sm:px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center">
                  <h3 className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2 text-sm">
                     Önce / Sonra Karşılaştırma
                  </h3>
                  <div className="flex items-center gap-2">
                     <span className="text-xs bg-indigo-50 dark:bg-indigo-900/40 text-indigo-700 dark:text-indigo-300 px-2.5 py-1 rounded-full font-medium border border-indigo-100 dark:border-indigo-800 capitalize">
                        {selectedStyle} Tarz
                     </span>
                  </div>
               </div>

               {/* Slider Area */}
               <div 
                  ref={sliderRef}
                  className="relative bg-slate-100 dark:bg-slate-800 min-h-[400px] sm:min-h-[500px] select-none cursor-ew-resize overflow-hidden group"
                  onMouseDown={onMouseDown}
                  onMouseMove={onMouseMove}
                  onTouchStart={onTouchStart}
                  onTouchMove={onTouchMove}
               >
                  {/* Before Image */}
                  <img 
                     src={result.originalImageUrl} 
                     alt="Before" 
                     className="absolute inset-0 w-full h-full object-cover pointer-events-none" 
                  />
                  <span className="absolute top-4 left-4 bg-black/60 text-white px-3 py-1.5 rounded-lg text-xs font-semibold z-[5] backdrop-blur-sm">
                     <EyeOff className="w-3 h-3 inline mr-1" /> Önce
                  </span>

                  {/* After Image (Clipped) */}
                  <div 
                     className="absolute top-0 left-0 bottom-0 overflow-hidden pointer-events-none"
                     style={{ width: `${sliderPosition}%` }}
                  >
                     <img 
                        src={result.stagedImageUrl} 
                        alt="After" 
                        className="absolute top-0 left-0 h-full max-w-none object-cover"
                        style={{ width: sliderRef.current ? sliderRef.current.clientWidth : '100%' }}
                     />
                     <span className="absolute top-4 right-4 bg-indigo-600/80 text-white px-3 py-1.5 rounded-lg text-xs font-semibold backdrop-blur-sm z-[5]" style={{ right: 'auto', left: `calc(${100/sliderPosition * 100}% - 4rem)` }}>
                        <Sparkles className="w-3 h-3 inline mr-1" /> Sonra
                     </span>
                  </div>

                  {/* Handle */}
                  <div 
                     className="absolute top-0 bottom-0 w-1 bg-white cursor-ew-resize z-10 shadow-[0_0_10px_rgba(0,0,0,0.5)]"
                     style={{ left: `${sliderPosition}%` }}
                  >
                     <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-10 h-10 bg-white rounded-full shadow-lg flex items-center justify-center">
                        <ChevronsLeftRight className="w-5 h-5 text-indigo-600" />
                     </div>
                  </div>
               </div>

               {/* Actions */}
               <div className="p-4 sm:p-5 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 flex flex-col sm:flex-row justify-between items-center gap-3">
                  <p className="text-xs text-slate-400 dark:text-slate-500">Staging tamamlandı</p>
                  <div className="flex gap-3 w-full sm:w-auto">
                     <Button variant="outline" onClick={() => setUploadedFile(null)} className="flex-1 sm:flex-none">
                        <RefreshCw className="w-4 h-4 mr-2" />
                        Farklı Tarz Dene
                     </Button>
                     <Button className="flex-1 sm:flex-none bg-emerald-600 hover:bg-emerald-700 text-white">
                        <Download className="w-4 h-4 mr-2" />
                        İndir (HD)
                     </Button>
                  </div>
               </div>
            </div>
         ) : (
            // Empty State
            <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden min-h-[520px] flex flex-col items-center justify-center p-8 text-center">
               <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center mb-4">
                  <ImageIcon className="w-8 h-8 text-slate-400 dark:text-slate-500" />
               </div>
               <h3 className="text-sm font-medium text-slate-700 dark:text-slate-300">Henüz fotoğraf yüklenmedi</h3>
               <p className="mt-1 text-xs text-slate-400 dark:text-slate-500 max-w-xs">Sol panelden bir fotoğraf yükleyip tarz seçerek başlayın.</p>
            </div>
         )}
      </div>
    </div>
  );
}
