"use client";

import { useState } from "react";
import { GeneratedListing, ToneType } from "@/types/listing";
import { Copy, RefreshCw, Palette, Eye, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

interface ListingTextResultProps {
  result: GeneratedListing | null;
  isLoading: boolean;
  onRegenerate: () => void;
  onChangeTone: (tone: ToneType) => void;
}

export function ListingTextResult({ result, isLoading, onRegenerate, onChangeTone }: ListingTextResultProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!result) return;
    try {
      const text = `${result.title}\n\n${result.description}`;
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("Failed to copy text: ", err);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden min-h-[500px] flex flex-col items-center justify-center p-8 space-y-4">
        <div className="relative">
          <div className="w-16 h-16 border-4 border-indigo-200 dark:border-indigo-800 rounded-full animate-spin border-t-indigo-600 dark:border-t-indigo-400"></div>
          <div className="absolute inset-0 flex items-center justify-center">
            <RefreshCw className="w-6 h-6 text-indigo-600 dark:text-indigo-400 animate-pulse" />
          </div>
        </div>
        <div className="text-center space-y-2">
          <h3 className="text-lg font-medium text-slate-700 dark:text-slate-300">İlan metniniz hazırlanıyor...</h3>
          <p className="text-sm text-slate-400 dark:text-slate-500">Bu işlem birkaç saniye sürebilir</p>
        </div>
        <div className="w-full max-w-sm space-y-3">
          <Skeleton className="h-4 w-3/4 mx-auto" />
          <Skeleton className="h-4 w-5/6 mx-auto" />
          <Skeleton className="h-4 w-2/3 mx-auto" />
        </div>
      </div>
    );
  }

  if (!result) {
    return (
      <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden min-h-[500px] flex flex-col items-center justify-center p-8 text-center space-y-4">
        <div className="w-16 h-16 bg-slate-100 dark:bg-slate-800 rounded-full flex items-center justify-center">
          <Eye className="w-8 h-8 text-slate-400 dark:text-slate-500" />
        </div>
        <div className="space-y-1">
          <h3 className="text-base font-medium text-slate-700 dark:text-slate-300">Henüz ilan metni oluşturulmadı</h3>
          <p className="text-sm text-slate-400 dark:text-slate-500 max-w-xs mx-auto">
            Sol paneldeki formu doldurup &quot;İlan Metni Oluştur&quot; butonuna tıklayın.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-800 shadow-sm overflow-hidden flex flex-col min-h-[500px] h-full">
      {/* Preview Header */}
      <div className="bg-slate-50 dark:bg-slate-800/50 px-5 sm:px-6 py-4 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center sticky top-0 z-10">
        <h3 className="font-semibold text-slate-800 dark:text-slate-200 flex items-center gap-2 text-sm">
          <Eye className="w-4 h-4 text-slate-500 dark:text-slate-400" />
          Önizleme
        </h3>
        <div className="flex items-center gap-2">
          <span className="text-xs text-indigo-700 dark:text-indigo-300 bg-indigo-50 dark:bg-indigo-900/40 border border-indigo-100 dark:border-indigo-800 px-2.5 py-1 rounded-full font-medium capitalize">
            {result.tone} Ton
          </span>
          <span className="text-xs text-slate-400 dark:text-slate-500">{result.wordCount} kelime</span>
        </div>
      </div>

      {/* Preview Content */}
      <div className="p-5 sm:p-6 flex-1 overflow-y-auto max-h-[calc(100vh-300px)]">
        <div className="space-y-6">
          {/* Title */}
          <div>
            <label className="block text-xs uppercase tracking-wider text-slate-400 dark:text-slate-500 font-semibold mb-2">İlan Başlığı</label>
            <h2 className="text-lg sm:text-xl font-bold text-slate-900 dark:text-slate-100 leading-tight">
              {result.title}
            </h2>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs uppercase tracking-wider text-slate-400 dark:text-slate-500 font-semibold mb-2">İlan Açıklaması</label>
            <div className="prose prose-sm dark:prose-invert text-slate-600 dark:text-slate-300 space-y-3 max-w-none whitespace-pre-wrap">
              {result.description}
            </div>
          </div>

          {/* Highlights */}
          {result.highlights && result.highlights.length > 0 && (
             <div>
                <label className="block text-xs uppercase tracking-wider text-slate-400 dark:text-slate-500 font-semibold mb-2">Öne Çıkanlar</label>
                <div className="flex flex-wrap gap-2">
                   {result.highlights.map((highlight, index) => (
                      <span key={index} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-100 text-emerald-800 dark:bg-emerald-900 dark:text-emerald-200">
                         {highlight}
                      </span>
                   ))}
                </div>
             </div>
          )}

           {/* SEO Keywords */}
           {result.seoKeywords && result.seoKeywords.length > 0 && (
             <div>
                <label className="block text-xs uppercase tracking-wider text-slate-400 dark:text-slate-500 font-semibold mb-2">SEO Anahtar Kelimeler</label>
                <div className="flex flex-wrap gap-2">
                   {result.seoKeywords.map((keyword, index) => (
                      <span key={index} className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200 border border-slate-200 dark:border-slate-700">
                         #{keyword}
                      </span>
                   ))}
                </div>
             </div>
          )}
        </div>
      </div>

      {/* Preview Actions */}
      <div className="p-4 sm:p-5 border-t border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 sticky bottom-0 z-10">
        <div className="grid grid-cols-3 gap-3">
          <Button
            variant="outline"
            onClick={onRegenerate}
            className="flex items-center gap-2"
          >
            <RefreshCw className="w-4 h-4" />
            <span className="hidden sm:inline">Yeniden Üret</span>
            <span className="sm:hidden">Yenile</span>
          </Button>
          
          <Button
             variant="outline"
             onClick={() => {
                const tones: ToneType[] = ['kurumsal', 'samimi', 'acil'];
                const currentIndex = tones.indexOf(result.tone);
                const nextTone = tones[(currentIndex + 1) % tones.length];
                onChangeTone(nextTone);
             }}
             className="flex items-center gap-2"
          >
             <Palette className="w-4 h-4" />
             <span className="hidden sm:inline">Tonu Değiştir</span>
             <span className="sm:hidden">Ton</span>
          </Button>

          <Button
            onClick={handleCopy}
            className={cn(
               "flex items-center gap-2 transition-all duration-200",
               copied ? "bg-green-600 hover:bg-green-700" : "bg-emerald-600 hover:bg-emerald-700"
            )}
          >
            {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
            <span className="hidden sm:inline">{copied ? "Kopyalandı" : "Metni Kopyala"}</span>
            <span className="sm:hidden">{copied ? "Tamam" : "Kopyala"}</span>
          </Button>
        </div>
      </div>
    </div>
  );
}
