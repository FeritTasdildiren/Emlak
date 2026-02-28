"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"

interface QuotaInfoProps {
  remaining: number
  limit: number
  className?: string
}

export function QuotaInfo({ remaining, limit, className }: QuotaInfoProps) {
  const percent = ((limit - remaining) / limit) * 100
  const isLow = remaining < 3
  const isEmpty = remaining === 0
  const color = isEmpty ? "bg-red-500" : isLow ? "bg-amber-500" : "bg-emerald-500"

  return (
    <Card className={cn("p-4 space-y-3 bg-zinc-50 dark:bg-zinc-900 border-zinc-200 dark:border-zinc-800", className)}>
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-zinc-900 dark:text-zinc-100">
          Değerleme Hakkı
        </h3>
        <span className="text-xs font-medium text-zinc-500 dark:text-zinc-400">
          {remaining}/{limit} kaldı
        </span>
      </div>

      {/* Progress Bar */}
      <div className="relative h-2 w-full rounded-full bg-zinc-200 dark:bg-zinc-700 overflow-hidden">
        <div
          className={cn("absolute inset-y-0 left-0 transition-all duration-500 ease-out", color)}
          style={{ width: `${percent}%` }}
        />
      </div>

      {isEmpty && (
        <Button size="sm" className="w-full mt-2 bg-indigo-600 hover:bg-indigo-700 text-white">
          Plan Yükselt
        </Button>
      )}
    </Card>
  )
}
