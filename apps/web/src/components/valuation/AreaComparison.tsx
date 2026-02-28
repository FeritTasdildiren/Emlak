"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Card } from "@/components/ui/card"

interface AreaComparisonProps {
  listingPrice: number
  areaAveragePrice: number
  className?: string
}

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency: "TRY",
    maximumFractionDigits: 0,
  }).format(amount)
}

export function AreaComparison({ listingPrice, areaAveragePrice, className }: AreaComparisonProps) {
  const diffPercent = ((listingPrice - areaAveragePrice) / areaAveragePrice) * 100
  const isAbove = diffPercent > 0
  const diffValue = Math.abs(diffPercent)
  
  // Calculate relative bar widths
  const maxVal = Math.max(listingPrice, areaAveragePrice)
  const listingWidth = (listingPrice / maxVal) * 100
  const areaWidth = (areaAveragePrice / maxVal) * 100

  return (
    <Card className={cn("p-6 space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Bölge Karşılaştırması
        </h3>
        {/* Badge */}
        <span
          className={cn(
            "text-xs font-semibold px-2 py-1 rounded-full",
            isAbove
              ? "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-300"
              : "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-300"
          )}
        >
          {isAbove ? "Ortalama Üzeri" : "Ortalama Altı"}
        </span>
      </div>

      <div className="text-sm text-zinc-500 dark:text-zinc-400">
        Bu mülkün değeri bölge ortalamasının{" "}
        <strong className={isAbove ? "text-red-600 dark:text-red-400" : "text-emerald-600 dark:text-emerald-400"}>
          %{diffValue.toFixed(1)} {isAbove ? "üzerinde" : "altında"}
        </strong>
        .
      </div>

      <div className="space-y-4 mt-4">
        {/* Row 1: Area Average */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs font-medium text-zinc-500 dark:text-zinc-400">
            <span>Bölge Ortalaması</span>
            <span>{formatCurrency(areaAveragePrice)}</span>
          </div>
          <div className="relative h-2.5 w-full bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
             <div 
                className="absolute inset-y-0 left-0 bg-zinc-400 dark:bg-zinc-600 rounded-full transition-all duration-1000 ease-out"
                style={{ width: `${areaWidth}%` }}
             />
          </div>
        </div>

        {/* Row 2: Listing Price */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs font-medium text-zinc-900 dark:text-zinc-100">
            <span>Sizin İlanınız</span>
            <span>{formatCurrency(listingPrice)}</span>
          </div>
          <div className="relative h-2.5 w-full bg-zinc-100 dark:bg-zinc-800 rounded-full overflow-hidden">
             <div 
                className={cn(
                    "absolute inset-y-0 left-0 rounded-full transition-all duration-1000 ease-out",
                    isAbove ? "bg-red-500" : "bg-emerald-500"
                )}
                style={{ width: `${listingWidth}%` }}
             />
          </div>
        </div>
      </div>
    </Card>
  )
}
