"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import type { ValuationResultData } from "./schema"
import { toast } from "@/components/ui/toast"

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function formatTL(amount: number): string {
  return new Intl.NumberFormat("tr-TR").format(amount) + " TL"
}

function formatKisaTL(amount: number): string {
  if (amount >= 1_000_000) {
    const m = (amount / 1_000_000).toFixed(2).replace(".", ",")
    return m + "M TL"
  }
  return formatTL(amount)
}

// Tailwind JIT: Tüm class'lar statik olmalı, runtime string manipülasyonu yapılmamalı (C12)
function getGuvenRenk(skor: number) {
  if (skor >= 80) return { bg: "bg-emerald-100 dark:bg-emerald-950", text: "text-emerald-700 dark:text-emerald-300", dot: "bg-emerald-700", label: "Yüksek" }
  if (skor >= 60) return { bg: "bg-amber-100 dark:bg-amber-950", text: "text-amber-700 dark:text-amber-300", dot: "bg-amber-700", label: "Orta" }
  return { bg: "bg-red-100 dark:bg-red-950", text: "text-red-700 dark:text-red-300", dot: "bg-red-700", label: "Düşük" }
}

// ---------------------------------------------------------------------------
// Price Range Bar
// ---------------------------------------------------------------------------

function PriceRangeBar({
  min,
  ort,
  max,
}: {
  min: number
  ort: number
  max: number
}) {
  const range = max - min
  const ortPercent = range > 0 ? ((ort - min) / range) * 100 : 50

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between text-xs font-medium text-zinc-500 dark:text-zinc-400">
        <span>Min: {formatKisaTL(min)}</span>
        <span>%80 Güven Aralığı</span>
        <span>Max: {formatKisaTL(max)}</span>
      </div>
      {/* Bar */}
      <div className="relative h-4 w-full rounded-full bg-zinc-100 dark:bg-zinc-800 overflow-hidden">
        {/* Gradient Background */}
        <div className="absolute inset-0 bg-gradient-to-r from-orange-300 via-orange-500 to-orange-700 opacity-20 dark:opacity-30" />
        
        {/* Active Range (visual representation) */}
        <div className="absolute inset-y-0 left-0 w-full bg-gradient-to-r from-transparent via-orange-500/20 to-transparent" />

        {/* Marker */}
        <div
          className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2 transition-all duration-1000 ease-out"
          style={{ left: `${Math.min(Math.max(ortPercent, 0), 100)}%` }}
        >
          <div className="h-6 w-1 bg-orange-600 dark:bg-orange-500 rounded-full shadow-[0_0_10px_rgba(234,88,12,0.5)]" />
        </div>
      </div>
      
      <div className="text-center">
         <span className="text-xs font-medium text-orange-600 dark:text-orange-400">
            Ortalama: {formatTL(ort)}
         </span>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Main Component
// ---------------------------------------------------------------------------

export interface ValuationResultProps {
  className?: string
  result: ValuationResultData | null
  loading?: boolean
  error?: string | null
  onReset?: () => void
}

export function ValuationResult({ className, result, loading, error, onReset }: ValuationResultProps) {
  // Animation state for count up
  const [displayPrice, setDisplayPrice] = React.useState(0)

  React.useEffect(() => {
    if (result) {
      const duration = 1000
      const steps = 60
      const stepValue = result.estimated_price / steps
      const interval = duration / steps
      
      let current = 0
      const timer = setInterval(() => {
        current += stepValue
        if (current >= result.estimated_price) {
          setDisplayPrice(result.estimated_price)
          clearInterval(timer)
        } else {
          setDisplayPrice(Math.round(current))
        }
      }, interval)
      
      return () => clearInterval(timer)
    } else {
      setDisplayPrice(0)
    }
  }, [result])

  const [downloading, setDownloading] = React.useState(false)

  const handleDownloadPdf = async () => {
    if (!result?.id) return

    setDownloading(true)
    try {
      const response = await fetch(`/api/v1/valuations/${result.id}/pdf`)
      
      if (!response.ok) throw new Error("PDF hazırlanamadı")
      
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `degerleme-raporu-${result.id}.pdf`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      console.error(err)
      // Opsiyonel: Kullaniciya hata gosterimi
      toast("PDF indirilemedi. Lütfen daha sonra tekrar deneyiniz.", "error")
    } finally {
      setDownloading(false)
    }
  }

  // 1. Loading State
  if (loading) {
     return (
       <div
        className={cn(
          "rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-700 dark:bg-zinc-900 p-6 flex flex-col space-y-6 min-h-[500px]",
          className
        )}
      >
        <div className="space-y-2 text-center animate-pulse">
            <div className="h-4 w-32 bg-zinc-200 dark:bg-zinc-800 rounded mx-auto" />
            <div className="h-8 w-48 bg-zinc-200 dark:bg-zinc-800 rounded mx-auto" />
        </div>
        <div className="h-4 w-full bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" />
        <div className="grid grid-cols-2 gap-4">
            <div className="h-24 bg-zinc-100 dark:bg-zinc-800 rounded-lg animate-pulse" />
            <div className="h-24 bg-zinc-100 dark:bg-zinc-800 rounded-lg animate-pulse" />
            <div className="h-24 bg-zinc-100 dark:bg-zinc-800 rounded-lg animate-pulse" />
            <div className="h-24 bg-zinc-100 dark:bg-zinc-800 rounded-lg animate-pulse" />
        </div>
        <div className="space-y-3">
             <div className="h-4 w-24 bg-zinc-200 dark:bg-zinc-800 rounded animate-pulse" />
             <div className="h-16 bg-zinc-100 dark:bg-zinc-800 rounded-lg animate-pulse" />
             <div className="h-16 bg-zinc-100 dark:bg-zinc-800 rounded-lg animate-pulse" />
        </div>
      </div>
     )
  }

  // 2. Error State
  if (error) {
      return (
        <div className={cn("rounded-xl border border-red-200 bg-red-50 p-8 text-center dark:border-red-900/50 dark:bg-red-900/20", className)}>
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-red-100 dark:bg-red-900/50">
                <svg className="h-6 w-6 text-red-600 dark:text-red-400" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008h-.008v-.008z" />
                </svg>
            </div>
            <h3 className="text-sm font-semibold text-red-800 dark:text-red-200">Bir Hata Oluştu</h3>
            <p className="mt-1 text-sm text-red-600 dark:text-red-300">{error}</p>
            <Button variant="outline" size="sm" onClick={onReset} className="mt-4 border-red-200 bg-white hover:bg-red-50 text-red-600 dark:border-red-800 dark:bg-transparent dark:hover:bg-red-900/30">
                Tekrar Dene
            </Button>
        </div>
      )
  }

  // 3. Empty State
  if (!result) {
    return (
      <div className={cn("rounded-xl border border-dashed border-zinc-300 bg-white p-8 text-center dark:border-zinc-700 dark:bg-zinc-900", className)}>
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-zinc-100 dark:bg-zinc-800">
          <svg
            className="h-8 w-8 text-zinc-400"
            fill="none"
            viewBox="0 0 24 24"
            strokeWidth={1.5}
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008zm0 3h.008v.008h-.008v-.008z"
            />
          </svg>
        </div>
        <h3 className="text-base font-semibold text-zinc-900 dark:text-zinc-100">Henüz Değerleme Yapılmadı</h3>
        <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
          Mülk bilgilerini doldurun ve &quot;Değerleme Yap&quot; butonuna tıklayarak sonucu burada görüntüleyin.
        </p>
      </div>
    )
  }

  // 4. Success State
  const { min_price, estimated_price, max_price, price_per_sqm, confidence, model_version, prediction_time_ms } = result
  const guven = getGuvenRenk(confidence)

  return (
    <div
      className={cn(
        "rounded-xl border border-zinc-200 bg-white shadow-sm dark:border-zinc-700 dark:bg-zinc-900 overflow-hidden animate-in fade-in duration-500 slide-in-from-bottom-4",
        className
      )}
    >
      {/* Header */}
      <div className="border-b border-zinc-200 px-6 py-4 dark:border-zinc-700 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Değerleme Sonucu
        </h2>
        <Badge variant="outline" className="text-xs font-normal text-zinc-500 border-zinc-200 dark:border-zinc-700">
            {model_version}
        </Badge>
      </div>

      {/* Body */}
      <div className="space-y-6 p-6">
        {/* Main Price Display */}
        <div className="text-center space-y-1">
          <div className="text-sm font-medium text-zinc-500 dark:text-zinc-400">
            Tahmini Piyasa Değeri
          </div>
          <div className="text-4xl font-bold font-mono text-zinc-900 dark:text-zinc-50 tracking-tight">
            {formatTL(displayPrice)}
          </div>
        </div>

         {/* Price Range Visual */}
        <div className="px-2">
            <PriceRangeBar min={min_price} ort={estimated_price} max={max_price} />
        </div>

        {/* Details Grid */}
        <div className="grid grid-cols-2 gap-3">
             {/* Unit Price */}
             <Card className="p-3 bg-zinc-50 dark:bg-zinc-800/50 border-zinc-100 dark:border-zinc-800 shadow-none">
                <div className="text-xs text-zinc-500 dark:text-zinc-400">m{"\u00B2"} Birim Fiyat</div>
                <div className="font-mono font-semibold text-zinc-900 dark:text-zinc-100 mt-1">
                    {new Intl.NumberFormat("tr-TR").format(price_per_sqm)} TL
                </div>
             </Card>

             {/* Confidence Score */}
             <Card className={cn("p-3 border-zinc-100 dark:border-zinc-800 shadow-none bg-zinc-50 dark:bg-zinc-800/50")}>
                <div className="text-xs text-zinc-500 dark:text-zinc-400">Güven Skoru</div>
                <div className="flex items-center gap-2 mt-1">
                    <span className={cn("inline-block w-2 h-2 rounded-full", guven.dot)}></span>
                    <span className="font-semibold text-zinc-900 dark:text-zinc-100">%{confidence}</span>
                    <span className={cn("text-[10px] px-1.5 py-0.5 rounded ml-auto", guven.bg, guven.text)}>{guven.label}</span>
                </div>
             </Card>

             {/* Model Version */}
             <Card className="p-3 bg-zinc-50 dark:bg-zinc-800/50 border-zinc-100 dark:border-zinc-800 shadow-none">
                 <div className="text-xs text-zinc-500 dark:text-zinc-400">Model Sürümü</div>
                 <div className="font-mono font-semibold text-zinc-900 dark:text-zinc-100 mt-1">
                     {model_version}
                 </div>
             </Card>
             
             {/* Prediction Time */}
             <Card className="p-3 bg-zinc-50 dark:bg-zinc-800/50 border-zinc-100 dark:border-zinc-800 shadow-none">
                 <div className="text-xs text-zinc-500 dark:text-zinc-400">Hesaplama Süresi</div>
                 <div className="font-mono font-semibold text-zinc-900 dark:text-zinc-100 mt-1">
                     {prediction_time_ms} ms
                 </div>
             </Card>
        </div>
      </div>

      {/* Footer Actions */}
      <div className="flex flex-col gap-2 border-t border-zinc-200 p-6 dark:border-zinc-700 bg-zinc-50/50 dark:bg-zinc-900/50">
        <Button
          type="button"
          size="lg"
          className="w-full bg-orange-600 text-white hover:bg-orange-700 focus-visible:ring-orange-600/20 shadow-sm"
          onClick={handleDownloadPdf}
          disabled={downloading}
        >
          {downloading ? (
            <>
              <svg className="mr-2 h-4 w-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              Hazırlanıyor...
            </>
          ) : (
            <>
              <svg
                className="mr-2 h-4 w-4"
                fill="none"
                viewBox="0 0 24 24"
                strokeWidth={1.5}
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
                />
              </svg>
              Detaylı Rapor İndir (PDF)
            </>
          )}
        </Button>
        <div className="flex gap-2">
            <Button
            type="button"
            variant="outline"
            className="flex-1 border-zinc-200 dark:border-zinc-700"
            onClick={onReset}
            >
            Yeni Değerleme
            </Button>
             <Button
            type="button"
            variant="outline"
            className="flex-1 border-zinc-200 dark:border-zinc-700"
            disabled
            title="Yakında"
            >
                <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M7.217 10.907a2.25 2.25 0 100 2.186m0-2.186c.18.324.283.696.283 1.093s-.103.77-.283 1.093m0-2.186l9.566-5.314m-9.566 7.5l9.566 5.314m0 0a2.25 2.25 0 103.935 2.186 2.25 2.25 0 00-3.935-2.186zm0-12.814a2.25 2.25 0 103.933-2.185 2.25 2.25 0 00-3.933 2.185z" />
                </svg>
                Paylaş
            </Button>
        </div>
      </div>
    </div>
  )
}