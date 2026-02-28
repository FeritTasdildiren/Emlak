/**
 * TG Mini App API Client
 *
 * Mevcut api-client.ts'yi saran, Telegram Mini App'e özel
 * ince bir katman. JWT token'ı localStorage'dan alır (use-tg-auth
 * tarafından konulan "token" key'i), 401/429/5xx için özel
 * Türkçe hata mesajları üretir.
 */

import { api, ApiError } from "@/lib/api-client";

// ================================================================
// Re-export ApiError for convenience
// ================================================================

export { ApiError };

// ================================================================
// Türkçe hata mesajları
// ================================================================

function humanizeError(err: unknown): string {
  if (err instanceof ApiError) {
    switch (err.status) {
      case 401:
        return "Oturumunuz sona erdi. Lütfen uygulamayı yeniden açın.";
      case 403:
        return "Bu işlemi gerçekleştirmek için yetkiniz yok.";
      case 429:
        return "Kota limitinize ulaştınız. Lütfen daha sonra tekrar deneyin.";
      case 404:
        return "İstenen kayıt bulunamadı.";
      case 422:
        return err.detail ?? "Girdiğiniz bilgileri kontrol edin.";
      default:
        if (err.status >= 500) {
          return "Sunucu hatası oluştu. Lütfen daha sonra tekrar deneyin.";
        }
        return err.detail ?? err.message;
    }
  }
  if (err instanceof Error) {
    return err.message;
  }
  return "Bilinmeyen bir hata oluştu.";
}

// ================================================================
// API Response Types
// ================================================================

/** Generic paginated response */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}

/** Credit balance */
export interface CreditBalance {
  credit_balance: number;
  plan_type: string;
}

/** Valuation request body */
export interface ValuationRequest {
  district: string;
  neighborhood?: string;
  property_type: string;
  net_sqm: number;
  gross_sqm?: number;
  room_count: number;
  living_room_count: number;
  floor: number;
  total_floors?: number;
  building_age: number;
  heating_type?: string;
}

/** Valuation API response */
export interface ValuationResponse {
  estimated_price: number;
  min_price: number;
  max_price: number;
  confidence: number;
  price_per_sqm: number;
  latency_ms: number;
  model_version: string;
  prediction_id: string;
  comparables: ComparableProperty[];
  quota_remaining: number;
  quota_limit: number;
  anomaly_warning?: string;
}

export interface ComparableProperty {
  property_id: string;
  distance_km: number;
  price_diff_percent: number;
  similarity_score: number;
  address: string;
  price: number;
  sqm: number;
  rooms: number;
}

/** Customer from API */
export interface ApiCustomer {
  id: string;
  full_name: string;
  phone: string | null;
  email: string | null;
  customer_type: "buyer" | "seller" | "renter" | "landlord";
  lead_status: "cold" | "warm" | "hot" | "converted" | "lost";
  budget_min: number | null;
  budget_max: number | null;
  desired_rooms: string | null;
  desired_area_min: number | null;
  desired_area_max: number | null;
  desired_districts: string[];
  tags: string[];
  source: string | null;
  notes: string | null;
  last_contact_at: string | null;
  created_at: string;
  updated_at: string;
}

/** Customer create body */
export interface CustomerCreateBody {
  full_name: string;
  phone?: string;
  email?: string;
  customer_type: "buyer" | "seller" | "renter" | "landlord";
  budget_min?: number;
  budget_max?: number;
  tags?: string[];
  source?: string;
  notes?: string;
}

/** Customer update body */
export interface CustomerUpdateBody {
  full_name?: string;
  phone?: string;
  email?: string;
  customer_type?: "buyer" | "seller" | "renter" | "landlord";
  budget_min?: number;
  budget_max?: number;
  tags?: string[];
  notes?: string;
}

/** Property from API */
export interface ApiProperty {
  id: string;
  title: string;
  district: string;
  neighborhood: string;
  price: number;
  net_sqm: number;
  rooms: string;
  created_at: string;
}

/** Match from API */
export interface ApiMatch {
  id: string;
  property_id: string;
  customer_id: string;
  score: number;
  status: "pending" | "interested" | "passed" | "contacted" | "converted";
  created_at: string;
}

// ================================================================
// API Functions
// ================================================================

/** Dashboard — portföy sayısı */
export async function fetchPropertyCount(): Promise<number> {
  const res = await api.get<PaginatedResponse<ApiProperty>>(
    "/properties?limit=1&offset=0",
  );
  return res.total;
}

/** Dashboard — müşteri sayısı */
export async function fetchCustomerCount(): Promise<number> {
  const res = await api.get<PaginatedResponse<ApiCustomer>>(
    "/customers?per_page=1&page=1",
  );
  return res.total;
}

/** Dashboard — eşleşme sayısı */
export async function fetchMatchCount(): Promise<number> {
  const res = await api.get<PaginatedResponse<ApiMatch>>(
    "/matches?per_page=1&page=1",
  );
  return res.total;
}

/** Dashboard — kredi/kota bilgisi */
export async function fetchCreditBalance(): Promise<CreditBalance> {
  return api.get<CreditBalance>("/credits/balance");
}

/** Değerleme — fiyat tahmini */
export async function submitValuation(
  data: ValuationRequest,
): Promise<ValuationResponse> {
  return api.post<ValuationResponse>("/valuations", data);
}

/** Müşteriler — liste */
export async function fetchCustomers(params: {
  page?: number;
  per_page?: number;
  search?: string;
  lead_status?: string;
}): Promise<PaginatedResponse<ApiCustomer>> {
  const searchParams = new URLSearchParams();
  if (params.page) searchParams.set("page", String(params.page));
  if (params.per_page) searchParams.set("per_page", String(params.per_page));
  if (params.search) searchParams.set("search", params.search);
  if (params.lead_status) searchParams.set("lead_status", params.lead_status);

  const qs = searchParams.toString();
  return api.get<PaginatedResponse<ApiCustomer>>(
    `/customers${qs ? `?${qs}` : ""}`,
  );
}

/** Müşteriler — yeni kayıt */
export async function createCustomer(
  data: CustomerCreateBody,
): Promise<ApiCustomer> {
  return api.post<ApiCustomer>("/customers", data);
}

/** Müşteriler — güncelle */
export async function updateCustomer(
  id: string,
  data: CustomerUpdateBody,
): Promise<ApiCustomer> {
  return api.patch<ApiCustomer>(`/customers/${id}`, data);
}

/** Müşteriler — lead status değiştir */
export async function updateLeadStatus(
  id: string,
  status: string,
): Promise<ApiCustomer> {
  return api.patch<ApiCustomer>(`/customers/${id}/status`, { status });
}

// ================================================================
// Error Utility (export for hooks)
// ================================================================

export { humanizeError };
