"use client"

import Link from "next/link"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { PropertyForm } from "@/components/properties/property-form"

export default function NewPropertyPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Link href="/properties">
          <Button variant="ghost" size="icon">
            <ArrowLeft className="h-5 w-5" />
          </Button>
        </Link>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Yeni İlan Ekle</h1>
          <p className="mt-1 text-sm text-gray-500">
            Portföyünüze yeni bir ilan ekleyin.
          </p>
        </div>
      </div>

      {/* Form */}
      <PropertyForm className="max-w-3xl" />
    </div>
  )
}
