"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { ArrowLeft } from "lucide-react"
import { Button } from "@/components/ui/button"
import { PropertyForm } from "@/components/properties/property-form"
import { PropertyFormValues } from "@/components/properties/property-form-schema"
import { useCreateProperty } from "@/hooks/use-properties"
import { toast } from "@/components/ui/toast"

export default function NewPropertyPage() {
  const router = useRouter()
  const createProperty = useCreateProperty()

  const handleSubmit = async (data: PropertyFormValues) => {
    try {
      const res = await createProperty.mutateAsync(data)
      toast("İlan başarıyla oluşturuldu.")
      router.push(`/properties/${res.id}`)
    } catch (error) {
      toast(error instanceof Error ? error.message : "İlan oluşturulurken bir hata oluştu.")
    }
  }

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
      <PropertyForm 
        className="max-w-3xl" 
        onSubmit={handleSubmit}
      />
    </div>
  )
}
