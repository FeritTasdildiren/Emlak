"use client";

import * as React from "react"
import { cn } from "@/lib/utils"
import { relativeTime } from "@/lib/utils/relative-time"

interface DataSource {
  source: string
  version: string
  fetched_at: string
  record_count?: number
}

export interface DataFreshnessTooltipProps extends React.HTMLAttributes<HTMLDivElement> {
  dataSources?: DataSource[]
  refreshStatus: string
  lastRefreshedAt?: string
  refreshError?: string
  children: React.ReactNode
}

export function DataFreshnessTooltip({
  dataSources = [],
  refreshStatus,
  lastRefreshedAt,
  refreshError,
  children,
  className,
  ...props
}: DataFreshnessTooltipProps) {
  const [isVisible, setIsVisible] = React.useState(false)

  return (
    <div 
      className={cn("relative inline-block cursor-help", className)}
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      {...props}
    >
      {children}
      
      {isVisible && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 bg-white dark:bg-zinc-950 border border-zinc-200 dark:border-zinc-800 rounded-lg shadow-lg z-50 text-sm animate-in fade-in zoom-in-95 duration-200">
          <div className="space-y-2">
            <div className="flex items-center justify-between border-b pb-1 mb-1 border-zinc-100 dark:border-zinc-800">
              <span className="font-semibold text-xs text-zinc-500 uppercase">Veri Detayı</span>
              {lastRefreshedAt && (
                <span className="text-xs text-zinc-400">{relativeTime(lastRefreshedAt)}</span>
              )}
            </div>
            
            {refreshError ? (
              <div className="text-red-600 dark:text-red-400 text-xs bg-red-50 dark:bg-red-900/10 p-2 rounded">
                <span className="font-semibold">Hata:</span> {refreshError}
              </div>
            ) : null}

            {dataSources && dataSources.length > 0 ? (
              <div className="space-y-2">
                {dataSources.map((ds, i) => (
                  <div key={i} className="text-xs bg-zinc-50 dark:bg-zinc-900 p-2 rounded border border-zinc-100 dark:border-zinc-800">
                    <div className="font-medium text-zinc-900 dark:text-zinc-100 flex justify-between items-center">
                      <span>{ds.source}</span>
                      <span className="text-[10px] bg-zinc-200 dark:bg-zinc-800 px-1 rounded text-zinc-600 dark:text-zinc-400">{ds.version}</span>
                    </div>
                    <div className="text-zinc-500 mt-1 flex justify-between items-center text-[10px]">
                      <span>{relativeTime(ds.fetched_at)} alındı</span>
                      {ds.record_count !== undefined && (
                        <span>{ds.record_count} kayıt</span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              !refreshError && <div className="text-xs text-zinc-500 italic">Kaynak detayları mevcut değil.</div>
            )}
          </div>
          {/* Arrow */}
          <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-[1px] border-8 border-transparent border-t-white dark:border-t-zinc-950 drop-shadow-sm pointer-events-none"></div>
        </div>
      )}
    </div>
  )
}
