import { z } from "zod"

export const valuationSchema = z.object({
  city: z.string().default("İstanbul"),
  district: z.string().min(1, "İlçe seçimi zorunlu"),
  neighborhood: z.string().optional(),
  property_type: z.enum(["daire", "villa", "mustakil", "isyeri"]),
  gross_sqm: z.number({ message: "Geçerli bir sayı giriniz" }).min(20, "En az 20 m² olmalıdır").max(1000, "En fazla 1000 m² olabilir"),
  net_sqm: z.number({ message: "Geçerli bir sayı giriniz" }).min(15, "En az 15 m² olmalıdır").max(900, "En fazla 900 m² olabilir"),
  room_count: z.string().min(1, "Oda sayısı seçimi zorunlu"), // "3+1" like string in the UI
  floor: z.string().min(1, "Kat seçimi zorunlu"), // string because of "çatı", "giriş" etc.
  building_age: z.string().min(1, "Bina yaşı seçimi zorunlu"),
  bathroom_count: z.string().min(1, "Banyo sayısı seçimi zorunlu"),
  has_balcony: z.boolean(),
  parking_type: z.enum(["acik", "kapali", "yok"]),
  has_elevator: z.boolean(),
  heating_type: z.string().min(1, "Isıtma tipi seçimi zorunlu"),
  facades: z.array(z.string()).optional(),
})

export type ValuationFormValues = z.infer<typeof valuationSchema>

export interface ValuationResultData {
  id: string
  estimated_price: number
  min_price: number
  max_price: number
  confidence: number
  price_per_sqm: number
  model_version: string
  prediction_time_ms: number
  area_average_price?: number
  quota_remaining: number
  quota_limit: number
  created_at?: string
  comparables: {
    id: string
    location: string
    sqm: number
    price: number
    similarity: number
    distance_km?: number
  }[]
}
