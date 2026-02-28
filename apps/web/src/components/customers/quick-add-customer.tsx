"use client"

import * as React from "react"
import { useForm, Controller } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { X } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Customer } from "@/types/customer"

// ---------------------------------------------------------------------------
// Schema
// ---------------------------------------------------------------------------

const quickAddSchema = z.object({
  full_name: z.string().min(2, "Ad soyad en az 2 karakter olmalıdır"),
  phone: z.string().optional(),
  customer_type: z.enum(["buyer", "renter"] as const),
})

type QuickAddValues = z.infer<typeof quickAddSchema>

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface QuickAddCustomerProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: (customer: Customer) => void
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function QuickAddCustomer({
  isOpen,
  onClose,
  onSuccess,
}: QuickAddCustomerProps) {
  const [loading, setLoading] = React.useState(false)

  const form = useForm<QuickAddValues>({
    resolver: zodResolver(quickAddSchema),
    defaultValues: {
      full_name: "",
      phone: "",
      customer_type: "buyer",
    },
  })

  const {
    register,
    handleSubmit,
    control,
    reset,
    formState: { errors },
  } = form

  // Reset form when modal opens
  React.useEffect(() => {
    if (isOpen) {
      reset()
    }
  }, [isOpen, reset])

  // Handle ESC key
  React.useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose()
      }
    }
    window.addEventListener("keydown", handleEsc)
    return () => window.removeEventListener("keydown", handleEsc)
  }, [isOpen, onClose])

  const onSubmit = async (data: QuickAddValues) => {
    setLoading(true)
    try {
      // Mock API call
      await new Promise((resolve) => setTimeout(resolve, 800))
      
      const newCustomer: Customer = {
        id: Math.random().toString(36).substr(2, 9),
        full_name: data.full_name,
        phone: data.phone,
        customer_type: data.customer_type,
        desired_districts: [],
        tags: [],
        lead_status: "cold",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      
      onSuccess(newCustomer)
      onClose()
    } catch (error) {
      console.error("Failed to create customer", error)
    } finally {
      setLoading(false)
    }
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div 
        className="relative w-full max-w-md rounded-lg bg-white p-6 shadow-xl dark:bg-zinc-900"
        role="dialog"
        aria-modal="true"
      >
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"
        >
          <X className="h-5 w-5" />
          <span className="sr-only">Kapat</span>
        </button>

        <h2 className="mb-6 text-xl font-semibold text-gray-900 dark:text-white">
          Hızlı Müşteri Ekle
        </h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <Input
            label="Ad Soyad *"
            placeholder="Örn: Mehmet Öz"
            autoFocus
            errorMessage={errors.full_name?.message}
            {...register("full_name")}
          />

          <Input
            label="Telefon"
            placeholder="0555 555 55 55"
            errorMessage={errors.phone?.message}
            {...register("phone")}
          />

          <div className="space-y-2">
            <label className="text-sm font-medium leading-none text-gray-900 dark:text-gray-100">
              Müşteri Tipi
            </label>
            <div className="flex rounded-lg bg-gray-100 p-1 dark:bg-gray-800">
              <Controller
                name="customer_type"
                control={control}
                render={({ field }) => (
                  <>
                    <button
                      type="button"
                      onClick={() => field.onChange("buyer")}
                      className={cn(
                        "flex-1 rounded-md py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600/20",
                        field.value === "buyer"
                          ? "bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-white"
                          : "text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
                      )}
                    >
                      Alıcı
                    </button>
                    <button
                      type="button"
                      onClick={() => field.onChange("renter")}
                      className={cn(
                        "flex-1 rounded-md py-1.5 text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-600/20",
                        field.value === "renter"
                          ? "bg-white text-gray-900 shadow-sm dark:bg-gray-700 dark:text-white"
                          : "text-gray-500 hover:text-gray-900 dark:text-gray-400 dark:hover:text-white"
                      )}
                    >
                      Kiracı
                    </button>
                  </>
                )}
              />
            </div>
            {errors.customer_type && (
              <p className="text-sm text-red-500">{errors.customer_type.message}</p>
            )}
          </div>

          <div className="flex gap-3 pt-2">
            <Button
              type="button"
              variant="outline"
              fullWidth
              onClick={onClose}
              disabled={loading}
            >
              İptal
            </Button>
            <Button type="submit" fullWidth loading={loading}>
              Kaydet
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
