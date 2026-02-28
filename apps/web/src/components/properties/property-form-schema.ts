import { z } from "zod"

// ---------------------------------------------------------------------------
// Mülk tipleri — property form için (konut alt tipleri dahil)
// ---------------------------------------------------------------------------

export const propertyTypeEnum = z.enum([
  "daire",
  "villa",
  "ofis",
  "arsa",
  "dukkan",
])

export type FormPropertyType = z.infer<typeof propertyTypeEnum>

// ---------------------------------------------------------------------------
// Ortak alanlar — tüm mülk tiplerinde zorunlu
// ---------------------------------------------------------------------------

const baseSchema = z.object({
  title: z
    .string()
    .min(5, "Başlık en az 5 karakter olmalıdır")
    .max(200, "Başlık en fazla 200 karakter olabilir"),
  description: z
    .string()
    .max(5000, "Açıklama en fazla 5000 karakter olabilir")
    .optional(),
  property_type: propertyTypeEnum,
  sub_category: z.string().optional(),
  listing_type: z.enum(["satilik", "kiralik"]),
  price: z
    .number({ message: "Fiyat giriniz" })
    .min(1, "Fiyat en az 1 olmalıdır"),
  currency: z.string(),
  city: z.string().min(1, "Şehir seçimi zorunludur"),
  district: z.string().min(1, "İlçe seçimi zorunludur"),
  neighborhood: z.string().optional(),
  address: z
    .string()
    .max(500, "Adres en fazla 500 karakter olabilir")
    .optional(),
  area_sqm: z
    .number({ message: "Alan giriniz" })
    .min(1, "Alan en az 1 m² olmalıdır")
    .max(50000, "Alan en fazla 50.000 m² olabilir"),
  status: z.enum(["active", "draft"]),
})

// ---------------------------------------------------------------------------
// Daire alanları
// ---------------------------------------------------------------------------

const daireFields = z.object({
  room_count: z.string().min(1, "Oda sayısı seçiniz"),
  floor: z.number().min(0).max(100).optional(),
  building_age: z.number().min(0).max(100).optional(),
  heating_type: z.string().optional(),
  has_balcony: z.boolean().optional(),
  has_elevator: z.boolean().optional(),
  has_parking: z.boolean().optional(),
  is_in_complex: z.boolean().optional(),
  is_furnished: z.boolean().optional(),
})

// ---------------------------------------------------------------------------
// Villa alanları
// ---------------------------------------------------------------------------

const villaFields = z.object({
  room_count: z.string().min(1, "Oda sayısı seçiniz"),
  total_floors: z.number().min(1).max(10).optional(),
  land_area: z.number().min(1).max(100000).optional(),
  building_age: z.number().min(0).max(100).optional(),
  has_pool: z.boolean().optional(),
  has_garden: z.boolean().optional(),
  has_garage: z.boolean().optional(),
  heating_type: z.string().optional(),
})

// ---------------------------------------------------------------------------
// Ofis alanları
// ---------------------------------------------------------------------------

const ofisFields = z.object({
  room_count: z.string().optional(),
  floor: z.number().min(0).max(100).optional(),
  building_age: z.number().min(0).max(100).optional(),
  open_area: z.number().min(0).optional(),
  closed_area: z.number().min(0).optional(),
  has_meeting_room: z.boolean().optional(),
  has_elevator: z.boolean().optional(),
  has_parking: z.boolean().optional(),
})

// ---------------------------------------------------------------------------
// Arsa alanları
// ---------------------------------------------------------------------------

const arsaFields = z.object({
  zoning_status: z.string().optional(),
  floor_permission: z.string().optional(),
  taks: z.number().min(0).max(1).optional(),
  kaks: z.number().min(0).max(10).optional(),
  road_frontage: z.number().min(0).optional(),
  infrastructure: z.array(z.string()).optional(),
})

// ---------------------------------------------------------------------------
// Dükkan alanları
// ---------------------------------------------------------------------------

const dukkanFields = z.object({
  floor: z.number().min(-5).max(100).optional(),
  showcase_length: z.number().min(0).optional(),
  building_age: z.number().min(0).max(100).optional(),
  has_storage: z.boolean().optional(),
})

// ---------------------------------------------------------------------------
// Dinamik şema — mülk tipine göre genişler
// ---------------------------------------------------------------------------

export function getPropertySchema(propertyType: FormPropertyType) {
  switch (propertyType) {
    case "daire":
      return baseSchema.merge(daireFields)
    case "villa":
      return baseSchema.merge(villaFields)
    case "ofis":
      return baseSchema.merge(ofisFields)
    case "arsa":
      return baseSchema.merge(arsaFields)
    case "dukkan":
      return baseSchema.merge(dukkanFields)
    default:
      return baseSchema
  }
}

// Supertype: tüm alanların birleşimidir (form state için)
export const fullPropertySchema = baseSchema
  .merge(daireFields.partial())
  .merge(villaFields.partial())
  .merge(ofisFields.partial())
  .merge(arsaFields.partial())
  .merge(dukkanFields.partial())

export type PropertyFormValues = z.infer<typeof fullPropertySchema>

// ---------------------------------------------------------------------------
// Tip-spesifik alan tanımları (UI'da hangi alanların gösterileceğini belirler)
// ---------------------------------------------------------------------------

export type FieldVisibility = Record<string, boolean>

export function getVisibleFields(propertyType: FormPropertyType): FieldVisibility {
  const common: FieldVisibility = {
    title: true,
    description: true,
    property_type: true,
    sub_category: true,
    listing_type: true,
    price: true,
    city: true,
    district: true,
    neighborhood: true,
    address: true,
    area_sqm: true,
    status: true,
  }

  switch (propertyType) {
    case "daire":
      return {
        ...common,
        room_count: true,
        floor: true,
        building_age: true,
        heating_type: true,
        has_balcony: true,
        has_elevator: true,
        has_parking: true,
        is_in_complex: true,
        is_furnished: true,
      }
    case "villa":
      return {
        ...common,
        room_count: true,
        total_floors: true,
        land_area: true,
        building_age: true,
        has_pool: true,
        has_garden: true,
        has_garage: true,
        heating_type: true,
      }
    case "ofis":
      return {
        ...common,
        room_count: true,
        floor: true,
        building_age: true,
        open_area: true,
        closed_area: true,
        has_meeting_room: true,
        has_elevator: true,
        has_parking: true,
      }
    case "arsa":
      return {
        ...common,
        zoning_status: true,
        floor_permission: true,
        taks: true,
        kaks: true,
        road_frontage: true,
        infrastructure: true,
      }
    case "dukkan":
      return {
        ...common,
        floor: true,
        showcase_length: true,
        building_age: true,
        has_storage: true,
      }
    default:
      return common
  }
}

// ---------------------------------------------------------------------------
// Resetlenecek alanlar — mülk tipi değiştiğinde sıfırlanır
// ---------------------------------------------------------------------------

export function getTypeSpecificDefaults(): Partial<PropertyFormValues> {
  return {
    room_count: undefined,
    floor: undefined,
    total_floors: undefined,
    building_age: undefined,
    heating_type: undefined,
    has_balcony: false,
    has_elevator: false,
    has_parking: false,
    is_in_complex: false,
    is_furnished: false,
    has_pool: false,
    has_garden: false,
    has_garage: false,
    land_area: undefined,
    open_area: undefined,
    closed_area: undefined,
    has_meeting_room: false,
    floor_permission: undefined,
    zoning_status: undefined,
    taks: undefined,
    kaks: undefined,
    road_frontage: undefined,
    infrastructure: [],
    showcase_length: undefined,
    has_storage: false,
    sub_category: undefined,
  }
}
