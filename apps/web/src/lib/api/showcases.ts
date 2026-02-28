import { api } from "@/lib/api-client";
import type { Showcase } from "@/types/showcase";
import type { Property } from "@/types/property";

// ─── Backend Response Types ──────────────────────────────────────

/** Backend PropertySummary (vitrin icindeki ilan ozeti) */
interface ApiPropertySummary {
  id: string;
  title: string | null;
  listing_type: string | null;
  property_type: string | null;
  price: number | null;
  currency: string | null;
  city: string | null;
  district: string | null;
  neighborhood: string | null;
  net_sqm: number | null;
  gross_sqm: number | null;
  room_count: string | null;
  building_age: number | null;
  floor_number: number | null;
  total_floors: number | null;
  photo_urls: string[];
}

/** Backend GET /showcases/public/{slug} yaniti */
interface ApiShowcasePublicResponse {
  slug: string;
  title: string;
  description: string | null;
  agent_phone: string | null;
  agent_email: string | null;
  agent_whatsapp: string | null;
  agent_photo_url: string | null;
  theme: string;
  properties: ApiPropertySummary[];
  views_count: number;
}

// ─── Mappers ─────────────────────────────────────────────────────

/** Backend theme string'ini frontend ShowcaseTheme'e donustur */
function mapTheme(theme: string): Showcase["theme"] {
  const themeMap: Record<string, Showcase["theme"]> = {
    modern: { primary_color: "#ea580c", background: "light", layout: "grid" },
    classic: { primary_color: "#0f172a", background: "dark", layout: "list" },
    minimal: { primary_color: "#1f2937", background: "light", layout: "grid" },
  };
  return themeMap[theme] ?? { primary_color: "#ea580c", background: "light", layout: "grid" };
}

/** Backend PropertySummary'yi frontend Property tipine donustur */
function mapPropertySummary(p: ApiPropertySummary): Property {
  return {
    id: p.id,
    title: p.title ?? "İsimsiz İlan",
    property_type: (p.property_type ?? "daire") as Property["property_type"],
    listing_type: (p.listing_type === "sale" ? "satilik" : p.listing_type === "rent" ? "kiralik" : (p.listing_type ?? "satilik")) as Property["listing_type"],
    price: p.price ?? 0,
    currency: p.currency ?? "TRY",
    area_sqm: p.net_sqm ?? p.gross_sqm ?? 0,
    room_count: p.room_count ? parseInt(p.room_count, 10) || null : null,
    floor: p.floor_number,
    total_floors: p.total_floors,
    building_age: p.building_age,
    city: p.city ?? "",
    district: p.district ?? "",
    neighborhood: p.neighborhood,
    address: null,
    status: "active" as Property["status"],
    created_at: "",
    updated_at: "",
  };
}

// ─── Public Exports ──────────────────────────────────────────────

export interface ShowcaseWithProperties extends Showcase {
  properties: Property[];
}

/**
 * Public vitrin verisini slug ile getirir.
 * Backend: GET /showcases/public/{slug} (JWT gereksiz)
 */
export async function fetchShowcaseBySlug(
  slug: string
): Promise<ShowcaseWithProperties | null> {
  try {
    const data = await api.get<ApiShowcasePublicResponse>(
      `/showcases/public/${encodeURIComponent(slug)}`
    );

    const theme = mapTheme(data.theme);

    return {
      id: "", // Public endpoint'te ID dondurulmuyor
      title: data.title,
      slug: data.slug,
      description: data.description ?? undefined,
      is_active: true, // Public endpoint sadece aktif vitrinleri dondurur
      views_count: data.views_count,
      selected_properties: data.properties.map((p) => p.id),
      agent: {
        name: "", // Public endpoint'te agent name yok, telefon/email var
        phone: data.agent_phone ?? undefined,
        email: data.agent_email ?? undefined,
        photo_url: data.agent_photo_url ?? undefined,
      },
      theme,
      created_at: "",
      updated_at: "",
      properties: data.properties.map(mapPropertySummary),
    };
  } catch (error: unknown) {
    // 404 = vitrin bulunamadi → null don
    if (error && typeof error === "object" && "status" in error && (error as { status: number }).status === 404) {
      return null;
    }
    throw error;
  }
}

/**
 * Vitrin goruntulenme sayacini arttirir.
 * Backend: POST /showcases/public/{slug}/view (JWT gereksiz)
 */
export async function incrementShowcaseViews(slug: string): Promise<void> {
  try {
    await api.post<{ views_count: number }>(
      `/showcases/public/${encodeURIComponent(slug)}/view`,
      {}
    );
  } catch {
    // View sayaci hatasini yutuyoruz — kullanici deneyimini bozmamali
    console.warn(`[showcases] View increment failed for slug: ${slug}`);
  }
}
