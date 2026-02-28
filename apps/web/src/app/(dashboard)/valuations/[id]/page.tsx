import { ValuationResult } from "@/components/valuation/ValuationResult"
import { ComparablesList } from "@/components/valuation/ComparablesList"
import { AreaComparison } from "@/components/valuation/AreaComparison"
import { getValuationById } from "@/lib/api/valuations"
import { notFound } from "next/navigation"

interface PageProps {
  params: Promise<{ id: string }>
}

export default async function ValuationDetailPage({ params }: PageProps) {
  const { id } = await params
  const valuation = await getValuationById(id)

  if (!valuation) {
    notFound()
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-zinc-900 dark:text-zinc-100">
            Değerleme Detayı
          </h1>
          <p className="mt-1 text-sm text-zinc-500 dark:text-zinc-400">
            #{valuation.id} numarali degerleme raporu
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-8 lg:grid-cols-3">
        {/* Main Result Column */}
        <div className="lg:col-span-1 space-y-6">
          <ValuationResult result={valuation} />
        </div>

        {/* Details Column */}
        <div className="lg:col-span-2 space-y-6">
          <ComparablesList 
             comparables={valuation.comparables} 
             estimatedPrice={valuation.estimated_price} 
          />
          <AreaComparison 
             listingPrice={valuation.estimated_price} 
             areaAveragePrice={valuation.area_average_price || valuation.estimated_price} 
          />
        </div>
      </div>
    </div>
  )
}
