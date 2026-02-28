import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { Check, AlertTriangle, Loader2, X } from "lucide-react"
import { relativeTime } from "@/lib/utils/relative-time"

const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      status: {
        fresh: "border-transparent bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400",
        stale: "border-transparent bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400",
        refreshing: "border-transparent bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400",
        failed: "border-transparent bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400",
      },
      size: {
        sm: "px-2 py-0.5 text-[10px]",
        md: "px-2.5 py-0.5 text-xs",
        lg: "px-3 py-1 text-sm",
      },
    },
    defaultVariants: {
      status: "fresh",
      size: "md",
    },
  }
)

export type DataFreshnessStatus = "fresh" | "stale" | "refreshing" | "failed"

export interface DataFreshnessBadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {
  status: DataFreshnessStatus
  lastRefreshedAt?: string
  showTimestamp?: boolean
}

export function DataFreshnessBadge({
  className,
  status,
  size,
  lastRefreshedAt,
  showTimestamp = false,
  ...props
}: DataFreshnessBadgeProps) {
  const statusConfig = {
    fresh: {
      label: "Güncel",
      icon: Check,
    },
    stale: {
      label: "Eski Veri",
      icon: AlertTriangle,
    },
    refreshing: {
      label: "Güncelleniyor...",
      icon: Loader2,
    },
    failed: {
      label: "Güncelleme Hatası",
      icon: X,
    },
  }

  const { label, icon: Icon } = statusConfig[status]

  return (
    <div className={cn(badgeVariants({ status, size }), className)} {...props}>
      <Icon className={cn("h-3 w-3", status === "refreshing" && "animate-spin")} />
      <span>{label}</span>
      {showTimestamp && lastRefreshedAt && status !== "refreshing" && (
        <span className="ml-1 opacity-70 font-normal border-l pl-1 border-current">
          {relativeTime(lastRefreshedAt)}
        </span>
      )}
    </div>
  )
}
