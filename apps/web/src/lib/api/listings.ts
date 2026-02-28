/**
 * Listings API — Gerçek backend endpoint'lerine bağlı.
 *
 * Endpoint'ler:
 *   GET  /listings/tones           → Ton listesi (public)
 *   POST /listings/generate-text   → AI ilan metni üretimi (JWT)
 *   POST /listings/regenerate-text → Farklı tonla yeniden üretim (JWT, kota tüketmez)
 *   GET  /listings/staging-styles  → Sahneleme tarzları (public)
 *   POST /listings/virtual-stage   → Virtual staging (JWT, multipart/form-data)
 *   POST /listings/analyze-room    → Oda analizi (JWT, multipart/form-data)
 *   POST /listings/export          → Portal export (JWT)
 */

import { api } from "@/lib/api-client";
import {
  ListingFormData,
  ListingTextResponse,
  ToneInfo,
  StyleInfo,
  StagingRequest,
  StagingResponse,
  PortalExportRequest,
  PortalExportResponse,
  RoomAnalysis,
} from "@/types/listing";

// ----------------------------------------------------------------
// Backend response tipleri (snake_case → camelCase mapping)
// ----------------------------------------------------------------

/** Backend ToneInfo modeli */
interface BackendToneInfo {
  id: string;
  name_tr: string;
  description: string;
  example_phrase: string;
}

/** Backend ToneListResponse */
interface BackendToneListResponse {
  tones: BackendToneInfo[];
  count: number;
}

/** Backend ListingTextResponse */
interface BackendListingTextResponse {
  title: string;
  description: string;
  highlights: string[];
  seo_keywords: string[];
  tone_used: string;
  token_usage: number;
}

/** Backend StyleInfo modeli */
interface BackendStyleInfo {
  id: string;
  name_tr: string;
  description: string;
}

/** Backend StyleListResponse */
interface BackendStyleListResponse {
  styles: BackendStyleInfo[];
  count: number;
}

/** Backend StagedImageItem */
interface BackendStagedImageItem {
  base64: string;
}

/** Backend RoomAnalysisResponse */
interface BackendRoomAnalysisResponse {
  room_type: string;
  is_empty: boolean;
  floor_type: string;
  estimated_size: string;
  wall_color: string;
  natural_light: string;
  window_count: number;
  special_features: string[];
}

/** Backend StagingResponse */
interface BackendStagingResponse {
  staged_images: BackendStagedImageItem[];
  room_analysis: BackendRoomAnalysisResponse;
  style: string;
  processing_time_ms: number;
}

/** Backend PortalExportResult */
interface BackendPortalExportResult {
  portal: string;
  formatted_title: string;
  formatted_description: string;
  character_counts: Record<string, number>;
  warnings: string[];
}

/** Backend PortalExportResponse */
interface BackendPortalExportResponse {
  exports: BackendPortalExportResult[];
}

// ----------------------------------------------------------------
// Ton ikonu eşlemesi (backend'de ikon yok, frontend ihtiyacı)
// ----------------------------------------------------------------

const TONE_ICON_MAP: Record<string, ToneInfo["iconName"]> = {
  kurumsal: "building",
  samimi: "heart",
  acil: "flame",
};

// ----------------------------------------------------------------
// API wrapper metotları
// ----------------------------------------------------------------

export const listingsApi = {
  /**
   * Kullanılabilir ilan tonlarını getirir.
   * GET /api/v1/listings/tones (Public)
   */
  getAvailableTones: async (): Promise<ToneInfo[]> => {
    const response = await api.get<BackendToneListResponse>("/listings/tones");
    return response.tones.map((t) => ({
      id: t.id as ToneInfo["id"],
      label: t.name_tr,
      description: t.description,
      iconName: TONE_ICON_MAP[t.id] ?? "building",
    }));
  },

  /**
   * AI destekli ilan metni üretir.
   * POST /api/v1/listings/generate-text (JWT)
   */
  generateListingText: async (data: ListingFormData): Promise<ListingTextResponse> => {
    const body = mapFormDataToBackend(data);
    const response = await api.post<BackendListingTextResponse>("/listings/generate-text", body);
    return mapBackendTextResponse(response);
  },

  /**
   * Aynı verilerle farklı tonla yeniden üretir — kota tüketmez.
   * POST /api/v1/listings/regenerate-text (JWT)
   */
  regenerateText: async (data: ListingFormData): Promise<ListingTextResponse> => {
    const body = mapFormDataToBackend(data);
    const response = await api.post<BackendListingTextResponse>("/listings/regenerate-text", body);
    return mapBackendTextResponse(response);
  },

  /**
   * Sahneleme tarzlarını getirir.
   * GET /api/v1/listings/staging-styles (Public)
   */
  getStagingStyles: async (): Promise<StyleInfo[]> => {
    const response = await api.get<BackendStyleListResponse>("/listings/staging-styles");
    return response.styles.map((s) => ({
      id: s.id as StyleInfo["id"],
      label: s.name_tr,
      description: s.description,
      // Backend'de imageUrl yok — placeholder kullan
      imageUrl: STYLE_IMAGE_MAP[s.id] ?? "",
    }));
  },

  /**
   * Boş oda fotoğrafını AI ile mobilyalı hale getirir.
   * POST /api/v1/listings/virtual-stage (JWT, multipart/form-data)
   */
  virtualStage: async (request: StagingRequest): Promise<StagingResponse> => {
    const formData = new FormData();
    formData.append("image", request.imageFile);
    formData.append("style", request.style);

    const response = await api.postFormData<BackendStagingResponse>("/listings/virtual-stage", formData);

    // Backend base64 PNG listesi döndürür, ilk görseli staged URL olarak kullan
    const stagedBase64 = response.staged_images[0]?.base64 ?? "";
    const stagedImageUrl = stagedBase64 ? `data:image/png;base64,${stagedBase64}` : "";

    return {
      originalImageUrl: URL.createObjectURL(request.imageFile),
      stagedImageUrl,
      analysis: {
        roomType: response.room_analysis.room_type,
        detectedObjects: response.room_analysis.special_features,
        lighting: response.room_analysis.natural_light,
      },
      creditsUsed: 5, // Backend kota sistemi üzerinden yönetiliyor
    };
  },

  /**
   * Oda fotoğrafını analiz eder (sahneleme yapmaz).
   * POST /api/v1/listings/analyze-room (JWT, multipart/form-data)
   */
  analyzeRoom: async (imageFile: File): Promise<RoomAnalysis> => {
    const formData = new FormData();
    formData.append("image", imageFile);

    const response = await api.postFormData<BackendRoomAnalysisResponse>("/listings/analyze-room", formData);

    return {
      roomType: response.room_type,
      detectedObjects: response.special_features,
      lighting: response.natural_light,
    };
  },

  /**
   * İlan metnini portal formatına çevirir.
   * POST /api/v1/listings/export (JWT)
   */
  exportToPortal: async (request: PortalExportRequest): Promise<PortalExportResponse> => {
    const body = {
      title: request.generatedText.title,
      description: request.generatedText.description,
      highlights: request.generatedText.highlights,
      portal: request.portals.length === 1 ? request.portals[0] : "both",
    };

    const response = await api.post<BackendPortalExportResponse>("/listings/export", body);

    return {
      success: true,
      portalPreview: response.exports.map((exp) => ({
        portal: exp.portal as PortalExportRequest["portals"][number],
        formattedContent: `<h1>${exp.formatted_title}</h1><p>${exp.formatted_description}</p>`,
      })),
    };
  },
};

// ----------------------------------------------------------------
// Yardımcı mapping fonksiyonları
// ----------------------------------------------------------------

/** Frontend ListingFormData → Backend ListingTextRequest body */
function mapFormDataToBackend(data: ListingFormData): Record<string, unknown> {
  return {
    property_type: data.propertyType,
    district: data.district,
    neighborhood: data.neighborhood ?? data.district,
    net_sqm: data.netSqm ?? data.grossSqm,
    room_count: data.roomCount ?? "3+1",
    price: 0, // Frontend formda price yok — backend zorunlu, 0 fallback
    gross_sqm: data.grossSqm > 0 ? data.grossSqm : undefined,
    floor: data.floor ?? undefined,
    total_floors: data.totalFloors ?? undefined,
    building_age: data.buildingAge ?? undefined,
    has_elevator: data.features.elevator || undefined,
    has_parking: data.features.parking || undefined,
    has_balcony: data.features.balcony || undefined,
    has_pool: data.features.pool || undefined,
    has_security: data.features.security || undefined,
    view_type: data.features.seaView ? "deniz" : undefined,
    additional_notes: data.additionalNotes || undefined,
    tone: data.tone,
  };
}

/** Backend ListingTextResponse → Frontend ListingTextResponse */
function mapBackendTextResponse(response: BackendListingTextResponse): ListingTextResponse {
  return {
    success: true,
    data: {
      title: response.title,
      description: response.description,
      tone: (response.tone_used as ListingFormData["tone"]) ?? "kurumsal",
      generatedAt: new Date().toISOString(),
      wordCount: response.description.split(/\s+/).length,
      highlights: response.highlights,
      seoKeywords: response.seo_keywords,
    },
    creditsUsed: 1,
    creditsRemaining: 0, // Backend kota sistemi üzerinden yönetiliyor
  };
}

/** Tarz görsel eşlemesi (backend'de imageUrl yok) */
const STYLE_IMAGE_MAP: Record<string, string> = {
  modern: "https://images.unsplash.com/photo-1502005229766-5283522a7f38?w=400&h=300&fit=crop",
  klasik: "https://images.unsplash.com/photo-1507089947368-19c1da9775ae?w=400&h=300&fit=crop",
  minimalist: "https://images.unsplash.com/photo-1493663284031-b7e3aefcae8e?w=400&h=300&fit=crop",
  skandinav: "https://images.unsplash.com/photo-1556228453-efd6c1ff04f6?w=400&h=300&fit=crop",
  bohem: "https://images.unsplash.com/photo-1522444195799-478538b28823?w=400&h=300&fit=crop",
  endustriyel: "https://images.unsplash.com/photo-1556912173-3db996ea0622?w=400&h=300&fit=crop",
};
