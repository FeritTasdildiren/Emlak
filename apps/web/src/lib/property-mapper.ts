import type { Property } from "@/types/property";
import type { PropertyFormValues } from "@/components/properties/property-form-schema";

/** Backend'den gelen property yapısı */
export interface ApiProperty {
  id: string;
  title: string;
  description?: string | null;
  property_type: string;
  listing_type: string;
  price: number;
  currency: string;
  rooms: string | null;
  gross_area: number | null;
  net_area: number | null;
  floor_number: number | null;
  total_floors: number | null;
  building_age: number | null;
  heating_type: string | null;
  bathroom_count: number | null;
  furniture_status: string | null;
  building_type: string | null;
  facade: string | null;
  city: string;
  district: string;
  neighborhood: string | null;
  address: string | null;
  latitude?: number | null;
  longitude?: number | null;
  photos: string[];
  status: string;
  created_at: string;
  updated_at: string;
}

/** Backend property verisini frontend Property tipine dönüştür */
export function mapApiToProperty(item: ApiProperty): Property {
  return {
    id: item.id,
    title: item.title,
    description: item.description,
    property_type: item.property_type as Property["property_type"],
    listing_type: (item.listing_type === "sale" ? "satilik" : "kiralik") as Property["listing_type"],
    price: item.price,
    currency: item.currency,
    area_sqm: item.net_area ?? item.gross_area ?? 0,
    room_count: item.rooms,
    floor: item.floor_number,
    total_floors: item.total_floors,
    building_age: item.building_age,
    heating_type: item.heating_type as Property["heating_type"],
    bathroom_count: item.bathroom_count,
    furniture_status: item.furniture_status as Property["furniture_status"],
    building_type: item.building_type as Property["building_type"],
    facade: item.facade as Property["facade"],
    city: item.city,
    district: item.district,
    neighborhood: item.neighborhood,
    address: item.address,
    latitude: item.latitude ?? null,
    longitude: item.longitude ?? null,
    status: (item.status === "active" ? "active" : item.status) as Property["status"],
    photos: item.photos,
    created_at: item.created_at,
    updated_at: item.updated_at,
  };
}

/** Frontend Property verisini backend API formatına dönüştür (Create/Update için) */
export function mapPropertyToApi(property: Partial<Property> | PropertyFormValues): Record<string, unknown> {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const apiData: Record<string, unknown> = { ...property } as any;

  // Field mapping: Frontend -> Backend
  if (property.listing_type) {
    apiData.listing_type = property.listing_type === "satilik" ? "sale" : "rent";
  }

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  if ((property as any).area_sqm !== undefined) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    apiData.net_area = (property as any).area_sqm;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    apiData.gross_area = (property as any).area_sqm; 
    delete apiData.area_sqm;
  }

  // room_count -> rooms
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  if ((property as any).room_count !== undefined) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    apiData.rooms = (property as any).room_count;
    delete apiData.room_count;
  }

  // floor -> floor_number
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  if ((property as any).floor !== undefined) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    apiData.floor_number = (property as any).floor;
    delete apiData.floor;
  }

  // latitude/longitude -> lat/lon
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  if ((property as any).latitude !== undefined || (property as any).longitude !== undefined) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    apiData.lat = (property as any).latitude ?? 41.0082;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    apiData.lon = (property as any).longitude ?? 28.9784;
    delete apiData.latitude;
    delete apiData.longitude;
  } else if (!apiData.lat) {
    apiData.lat = 41.0082;
    apiData.lon = 28.9784;
  }

  // bathroom_count can be string from form, convert to number
  if (typeof apiData.bathroom_count === "string") {
    apiData.bathroom_count = parseInt(apiData.bathroom_count, 10) || null;
  }
  
  return apiData;
}

/** Frontend Property verisini PropertyFormValues tipine dönüştür (Edit formu için) */
export function mapPropertyToFormValues(property: Property): Partial<PropertyFormValues> {
  return {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ...(property as any),
    room_count: property.room_count ?? undefined,
    bathroom_count: property.bathroom_count?.toString() ?? undefined,
    floor: property.floor ?? undefined,
    total_floors: property.total_floors ?? undefined,
    building_age: property.building_age ?? undefined,
    listing_type: property.listing_type as PropertyFormValues["listing_type"],
    property_type: property.property_type as PropertyFormValues["property_type"],
    status: (property.status === "active" ? "active" : "draft") as PropertyFormValues["status"],
    // Add any other specific mappings if needed
  };
}
