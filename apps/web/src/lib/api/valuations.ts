import { api } from "@/lib/api-client";
import type { ValuationFormValues, ValuationResultData } from "@/components/valuation/schema";

// ─── Backend Response Types ──────────────────────────────────────

/** POST /valuations backend yanıtı */
interface ValuationApiResponse {
  estimated_price: number;
  min_price: number;
  max_price: number;
  confidence: number; // 0-1 aralığı
  price_per_sqm: number;
  latency_ms: number;
  model_version: string;
  prediction_id: string;
  comparables: ApiComparable[];
  quota_remaining: number;
  quota_limit: number;
  anomaly_warning?: string | null;
}

interface ApiComparable {
  property_id: string;
  distance_km: number | null;
  price_diff_percent: number;
  similarity_score: number; // 0-100
  address: string | null;
  price: number;
  sqm: number;
  rooms: string | null;
}

/** GET /valuations backend liste öğesi */
interface ValuationListItem {
  id: string;
  predicted_price: number;
  confidence_low: number;
  confidence_high: number;
  created_at: string;
  model_version: string;
}

/** GET /valuations backend liste yanıtı */
interface ValuationListApiResponse {
  items: ValuationListItem[];
  total: number;
  limit: number;
  offset: number;
}

/** GET /valuations/{id} backend detay yanıtı */
interface ValuationDetailApiResponse {
  id: string;
  predicted_price: number;
  confidence_low: number;
  confidence_high: number;
  confidence: number | null;
  model_version: string;
  latency_ms: number | null;
  input_features: Record<string, unknown>;
  output_data: Record<string, unknown>;
  created_at: string;
}

// ─── Mapping Helpers ─────────────────────────────────────────────

/** POST yanıtı → frontend ValuationResultData */
function mapPostResponse(res: ValuationApiResponse): ValuationResultData {
  return {
    id: res.prediction_id,
    estimated_price: res.estimated_price,
    min_price: res.min_price,
    max_price: res.max_price,
    confidence: Math.round(res.confidence * 100), // 0-1 → 0-100
    price_per_sqm: res.price_per_sqm,
    model_version: res.model_version,
    prediction_time_ms: res.latency_ms,
    quota_remaining: res.quota_remaining,
    quota_limit: res.quota_limit,
    comparables: res.comparables.map((c) => ({
      id: c.property_id,
      location: c.address ?? "Bilinmiyor",
      sqm: c.sqm,
      price: c.price,
      similarity: c.similarity_score,
      distance_km: c.distance_km ?? undefined,
    })),
  };
}

/** Liste öğesi → frontend ValuationResultData (sınırlı veri) */
function mapListItem(item: ValuationListItem): ValuationResultData {
  return {
    id: item.id,
    estimated_price: item.predicted_price,
    min_price: item.confidence_low,
    max_price: item.confidence_high,
    confidence: 85, // Liste endpoint'i confidence döndürmüyor, varsayılan
    price_per_sqm: 0,
    model_version: item.model_version,
    prediction_time_ms: 0,
    quota_remaining: 0,
    quota_limit: 0,
    comparables: [],
    created_at: item.created_at,
  };
}

/** Detay yanıtı → frontend ValuationResultData */
function mapDetailResponse(res: ValuationDetailApiResponse): ValuationResultData {
  // output_data içinden ekstra bilgileri çıkar
  const output = res.output_data ?? {};
  const pricePerSqm = typeof output.price_per_sqm === "number" ? output.price_per_sqm : 0;
  const comparables = Array.isArray(output.comparables)
    ? output.comparables.map((c: Record<string, unknown>) => ({
        id: String(c.property_id ?? c.id ?? ""),
        location: String(c.address ?? c.location ?? "Bilinmiyor"),
        sqm: Number(c.sqm ?? 0),
        price: Number(c.price ?? 0),
        similarity: Number(c.similarity_score ?? c.similarity ?? 0),
        distance_km: c.distance_km != null ? Number(c.distance_km) : undefined,
      }))
    : [];

  return {
    id: res.id,
    estimated_price: res.predicted_price,
    min_price: res.confidence_low,
    max_price: res.confidence_high,
    confidence: res.confidence != null ? Math.round(res.confidence * 100) : 85,
    price_per_sqm: pricePerSqm as number,
    model_version: res.model_version,
    prediction_time_ms: res.latency_ms ?? 0,
    quota_remaining: 0,
    quota_limit: 0,
    comparables,
    created_at: res.created_at,
  };
}

// ─── Form değerlerini backend request'e dönüştürme ──────────────

function mapFormToRequest(data: ValuationFormValues): Record<string, unknown> {
  // room_count: "3+1" → room_count=3, living_room_count=1
  const roomParts = (data.room_count ?? "3+1").split("+");
  const roomCount = parseInt(roomParts[0], 10) || 3;
  const livingRoomCount = roomParts.length > 1 ? parseInt(roomParts[1], 10) || 1 : 1;

  // floor: string → int
  let floor = 0;
  const floorStr = (data.floor ?? "").toLowerCase();
  if (floorStr === "giris" || floorStr === "giriş" || floorStr === "zemin") {
    floor = 0;
  } else if (floorStr === "bodrum") {
    floor = -1;
  } else if (floorStr === "cati" || floorStr === "çatı") {
    floor = 10;
  } else {
    floor = parseInt(floorStr, 10) || 0;
  }

  // building_age: string range → orta değer
  let buildingAge = 5;
  const ageStr = data.building_age ?? "";
  if (ageStr === "0" || ageStr === "0-1") buildingAge = 0;
  else if (ageStr === "1-5") buildingAge = 3;
  else if (ageStr === "6-10") buildingAge = 8;
  else if (ageStr === "11-15") buildingAge = 13;
  else if (ageStr === "16-20") buildingAge = 18;
  else if (ageStr === "21-25") buildingAge = 23;
  else if (ageStr === "25+") buildingAge = 30;
  else buildingAge = parseInt(ageStr, 10) || 5;

  // property_type mapping
  const typeMap: Record<string, string> = {
    daire: "Daire",
    villa: "Villa",
    mustakil: "Mustakil",
    isyeri: "IsYeri",
  };

  return {
    district: data.district,
    neighborhood: data.neighborhood || data.district,
    property_type: typeMap[data.property_type] || "Daire",
    net_sqm: data.net_sqm,
    gross_sqm: data.gross_sqm || Math.round(data.net_sqm * 1.2),
    room_count: roomCount,
    living_room_count: livingRoomCount,
    floor,
    total_floors: floor + 5,
    building_age: buildingAge,
    heating_type: data.heating_type || "Kombi",
  };
}

// ─── Public API Fonksiyonları ────────────────────────────────────

/** Yeni değerleme gönder */
export async function submitValuation(data: ValuationFormValues): Promise<ValuationResultData> {
  const requestBody = mapFormToRequest(data);
  const response = await api.post<ValuationApiResponse>("/valuations", requestBody);
  return mapPostResponse(response);
}

/** Değerleme geçmişi listesi */
export async function getValuations(
  page = 1,
  limit = 10
): Promise<{ data: ValuationResultData[]; total: number }> {
  const offset = (page - 1) * limit;
  const response = await api.get<ValuationListApiResponse>(
    `/valuations?limit=${limit}&offset=${offset}`
  );
  return {
    data: response.items.map(mapListItem),
    total: response.total,
  };
}

/** Tek değerleme detayı */
export async function getValuationById(id: string): Promise<ValuationResultData | null> {
  try {
    const response = await api.get<ValuationDetailApiResponse>(`/valuations/${id}`);
    return mapDetailResponse(response);
  } catch (err) {
    // 404 durumunda null dön
    if (err && typeof err === "object" && "status" in err && (err as { status: number }).status === 404) {
      return null;
    }
    throw err;
  }
}


/** Kota durumu */
export async function getQuotaStatus(): Promise<{ remaining: number; limit: number }> {
  try {
    // Son degerlemeyi cekip kota bilgisini kullan
    const response = await api.get<ValuationListApiResponse>("/valuations?limit=1&offset=0");
    // Eger hic degerleme yoksa varsayilan kota don
    if (response.total === 0) {
      return { remaining: 10, limit: 10 };
    }
    // Backend'de kota bilgisi sadece POST yaniti ile geliyor
    // Fallback: limit - kullanim sayisi
    return { remaining: Math.max(0, 50 - response.total), limit: 50 };
  } catch {
    // Hata durumunda varsayilan
    return { remaining: 10, limit: 10 };
  }
}
