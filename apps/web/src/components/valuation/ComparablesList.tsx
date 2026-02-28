"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Card } from "@/components/ui/card"
import type { ValuationResultData } from "./schema"

interface ComparablesListProps {
  comparables: ValuationResultData["comparables"]
  estimatedPrice: number
  className?: string
}

function formatCurrency(amount: number) {
  return new Intl.NumberFormat("tr-TR", {
    style: "currency",
    currency: "TRY",
    maximumFractionDigits: 0,
  }).format(amount)
}

export function ComparablesList({ comparables, estimatedPrice, className }: ComparablesListProps) {
  if (!comparables?.length) return null

  return (
    <Card className={cn("p-6 space-y-4", className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-zinc-900 dark:text-zinc-100">
          Emsal Mülk Karşılaştırması
        </h3>
        <span className="text-xs text-zinc-500 bg-zinc-100 dark:bg-zinc-800 px-2 py-1 rounded-full">
          {comparables.length} Emsal
        </span>
      </div>

      <div className="space-y-3">
        {comparables.map((comp) => {
          const diffPercent = ((comp.price - estimatedPrice) / estimatedPrice) * 100
          const isHigher = diffPercent > 0
          const diffColor = isHigher ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"
          
          return (
            <div
              key={comp.id}
              className="group flex flex-col sm:flex-row sm:items-center justify-between gap-4 rounded-lg border border-zinc-100 bg-zinc-50/50 p-4 transition-all hover:bg-white hover:shadow-sm dark:border-zinc-800 dark:bg-zinc-900/50 dark:hover:bg-zinc-900"
            >
              {/* Left: Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                   <h4 className="font-medium text-zinc-900 dark:text-zinc-100 truncate">
                      {comp.location}
                   </h4>
                   <span className="shrink-0 text-[10px] font-medium px-1.5 py-0.5 rounded bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
                      %{comp.similarity} Benzer
                   </span>
                </div>
                
                <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-zinc-500 dark:text-zinc-400">
                  <span className="flex items-center gap-1">
                    <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                    </svg>
                    {comp.sqm} m²
                  </span>
                  <span className="w-1 h-1 rounded-full bg-zinc-300 dark:bg-zinc-600" />
                  <span className="flex items-center gap-1">
                     <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                     </svg>
                     {comp.distance_km ? `${comp.distance_km} km` : '? km'}
                  </span>
                </div>
              </div>

              {/* Right: Price & Diff */}
              <div className="flex flex-row sm:flex-col items-center sm:items-end justify-between sm:justify-center gap-2 sm:gap-0 text-right">
                 <div className="font-mono font-semibold text-zinc-900 dark:text-zinc-100">
                    {formatCurrency(comp.price)}
                 </div>
                 <div className={cn("text-xs font-medium flex items-center gap-1", diffColor)}>
                    {isHigher ? (
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" />
                        </svg>
                    ) : (
                        <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                        </svg>
                    )}
                    <span>
                       {isHigher ? '+' : ''}{diffPercent.toFixed(1)}%
                    </span>
                 </div>
              </div>
            </div>
          )
        })}
      </div>
    </Card>
  )
}
