"use client"

import * as React from "react"
import Link from "next/link"
import { cn } from "@/lib/utils"
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableHead, 
  TableHeader, 
  TableRow 
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button, buttonVariants } from "@/components/ui/button"
import { getValuations } from "@/lib/api/valuations"
import type { ValuationResultData } from "./schema"

// Helper for formatting currency
const formatCurrency = (value: number) => 
  new Intl.NumberFormat("tr-TR", { style: "currency", currency: "TRY", maximumFractionDigits: 0 }).format(value)

// Helper for formatting date
const formatDate = (dateString: string | number | Date) => {
    return new Intl.DateTimeFormat("tr-TR", { 
        day: "numeric", 
        month: "short", 
        year: "numeric", 
        hour: "2-digit", 
        minute: "2-digit" 
    }).format(new Date(dateString))
}

export function ValuationHistory() {
  const [data, setData] = React.useState<ValuationResultData[]>([])
  const [loading, setLoading] = React.useState(true)
  const [page, setPage] = React.useState(1)
  const [hasMore, setHasMore] = React.useState(true)

  React.useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      try {
        const result = await getValuations(page)
        setData(result.data)
        // Mock pagination logic
        setHasMore(result.total > page * 10)
      } catch (error) {
        console.error("Gecmis degerlemeler yuklenemedi", error)
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [page])

  if (loading && data.length === 0) {
    return (
      <div className="space-y-4">
        <div className="h-8 w-48 bg-zinc-100 dark:bg-zinc-800 rounded animate-pulse" />
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <div key={i} className="h-12 w-full bg-zinc-50 dark:bg-zinc-900 rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="rounded-md border border-zinc-200 dark:border-zinc-800">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Tarih</TableHead>
            <TableHead>Tahmin Fiyat</TableHead>
            <TableHead>Güven Aralığı</TableHead>
            <TableHead>Model</TableHead>
            <TableHead className="text-right">Islem</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {data.map((item) => (
            <TableRow key={item.id}>
              <TableCell className="font-medium">
                {/* Mocking date since it's not in schema but added in mock return */}
                {formatDate(item.created_at || Date.now())}
              </TableCell>
              <TableCell>{formatCurrency(item.estimated_price)}</TableCell>
              <TableCell>
                <Badge variant={item.confidence > 80 ? "default" : item.confidence > 60 ? "secondary" : "destructive"}>
                  %{item.confidence}
                </Badge>
              </TableCell>
              <TableCell className="text-zinc-500">{item.model_version}</TableCell>
              <TableCell className="text-right">
                <Link
                  href={`/valuation/${item.id}`}
                  className={cn(buttonVariants({ variant: "ghost", size: "sm" }))}
                >
                    Detay
                </Link>
              </TableCell>
            </TableRow>
          ))}
          {data.length === 0 && (
            <TableRow>
              <TableCell colSpan={5} className="h-24 text-center">
                Henuz gecmis bir degerleme bulunmuyor.
              </TableCell>
            </TableRow>
          )}
        </TableBody>
      </Table>
      
      {/* Pagination controls could go here */}
      <div className="flex items-center justify-end space-x-2 py-4 px-4 border-t border-zinc-200 dark:border-zinc-800">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          disabled={page === 1 || loading}
        >
          Onceki
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => setPage((p) => p + 1)}
          disabled={!hasMore || loading}
        >
          Sonraki
        </Button>
      </div>
    </div>
  )
}
