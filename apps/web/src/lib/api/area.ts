const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface AreaAnalysisResponse {
  id: string;
  city: string;
  district: string;
  neighborhood?: string;
  avg_price_sqm_sale?: number;
  avg_price_sqm_rent?: number;
  price_trend_6m?: number;
  supply_demand_ratio?: number;
  listing_count?: number;
  population?: number;
  transport_score?: number;
  amenity_score?: number;
  investment_score?: number;
  amortization_years?: number;
  refresh_status: "fresh" | "stale" | "refreshing" | "failed";
  data_sources: Array<{
    source: string;
    version: string;
    fetched_at: string;
    record_count: number;
  }>;
  last_refreshed_at?: string;
  refresh_error?: string;
}

export interface DepremRiskResponse {
  risk_score: number;
  pga_value?: number;
  soil_class?: string;
  building_code_era?: string;
  fault_distance_km?: number;
  refresh_status: "fresh" | "stale" | "refreshing" | "failed";
  data_sources: Array<{ source: string; version: string; fetched_at: string }>;
  last_refreshed_at?: string;
}

export interface TrendItem {
  month: string;
  price_sqm_sale: number;
  price_sqm_rent: number;
}

export interface PriceTrendResponse {
  trends: TrendItem[];
  change_pct_sale: number;
  change_pct_rent: number;
}

export interface CompareAreaItem {
  city: string;
  district: string;
  avg_price_sqm_sale: number;
  avg_price_sqm_rent: number;
  population: number;
  investment_score: number;
  transport_score: number;
  rental_yield_annual_pct: number;
  amortization_years: number;
}

export interface CompareResponse {
  areas: CompareAreaItem[];
  count: number;
}

export async function fetchAreaAnalysis(city: string, district: string): Promise<AreaAnalysisResponse> {
  const res = await fetch(`${API_BASE}/areas/${encodeURIComponent(city)}/${encodeURIComponent(district)}`);
  if (!res.ok) throw new Error(`Area analysis fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchDepremRisk(city: string, district: string): Promise<DepremRiskResponse> {
  const res = await fetch(`${API_BASE}/deprem-risk/${encodeURIComponent(city)}/${encodeURIComponent(district)}`);
  if (!res.ok) throw new Error(`Deprem risk fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchAreaCompare(districts: string[]): Promise<CompareResponse> {
  const params = new URLSearchParams();
  params.append("districts", districts.join(","));
  const res = await fetch(`${API_BASE}/areas/compare?${params.toString()}`);
  if (!res.ok) throw new Error(`Compare fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchAreaTrends(city: string, district: string, months?: number): Promise<PriceTrendResponse> {
  const params = months ? `?months=${months}` : '';
  const res = await fetch(`${API_BASE}/areas/${encodeURIComponent(city)}/${encodeURIComponent(district)}/trends${params}`);
  if (!res.ok) throw new Error(`Trends fetch failed: ${res.status}`);
  return res.json();
}