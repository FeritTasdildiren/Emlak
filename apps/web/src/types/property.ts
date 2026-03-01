export type PropertyType = "daire" | "villa" | "ofis" | "arsa" | "dukkan";
export type ListingType = "satilik" | "kiralik";
export type PropertyStatus = "active" | "sold" | "rented" | "draft";

export type HeatingType =
  | "dogalgaz_kombi"
  | "dogalgaz_merkezi"
  | "merkezi_pay_olcer"
  | "klima"
  | "soba"
  | "yerden_isitma"
  | "yok";

export type FurnitureStatus = "bos" | "esyali" | "yari_esyali";

export type BuildingType =
  | "betonarme"
  | "celik"
  | "ahsap"
  | "prefabrik"
  | "tas"
  | "tugla";

export type Facade =
  | "kuzey"
  | "guney"
  | "dogu"
  | "bati"
  | "kuzey_dogu"
  | "kuzey_bati"
  | "guney_dogu"
  | "guney_bati";

export interface Property {
  id: string;
  title: string;
  property_type: PropertyType;
  listing_type: ListingType;
  price: number;
  currency: string;
  area_sqm: number;
  room_count: string | null;
  floor: number | null;
  total_floors: number | null;
  building_age: number | null;
  heating_type: HeatingType | null;
  bathroom_count: number | null;
  furniture_status: FurnitureStatus | null;
  building_type: BuildingType | null;
  facade: Facade | null;
  city: string;
  district: string;
  neighborhood: string | null;
  address: string | null;
  status: PropertyStatus;
  created_at: string;
  updated_at: string;
}

export interface PropertyFilters {
  search: string;
  property_type: PropertyType | "all";
  status: PropertyStatus | "all";
  page: number;
  per_page: number;
}

export interface SearchFilters {
  q: string;
  city: string;
  district: string;
  property_type: PropertyType | "all";
  listing_type: ListingType | "all";
  status: PropertyStatus | "all";
  min_price?: number;
  max_price?: number;
  min_area?: number;
  max_area?: number;
  sort: string;
  page: number;
  per_page: number;
}

export interface SearchResponse {
  items: Property[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
  query: string;
}

export interface SuggestionsResponse {
  suggestions: string[];
}

export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
