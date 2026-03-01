import { api } from "../api-client";

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
  investment_metrics?: {
    kira_verimi?: number;
    amortisman_yil?: number;
  };
}

export interface CompareResponse {
  areas: CompareAreaItem[];
  count: number;
}

export async function fetchAreaAnalysis(city: string, district: string): Promise<AreaAnalysisResponse> {
  return api.get<AreaAnalysisResponse>(`/areas/${encodeURIComponent(city)}/${encodeURIComponent(district)}`);
}

export async function fetchDepremRisk(district: string): Promise<DepremRiskResponse> {
  return api.get<DepremRiskResponse>(`/earthquake/risk/${encodeURIComponent(district)}`);
}

export async function fetchAreaCompare(districts: string[]): Promise<CompareResponse> {
  const params = new URLSearchParams();
  params.append("districts", districts.join(","));
  return api.get<CompareResponse>(`/areas/compare?${params.toString()}`);
}

export async function fetchAreaTrends(city: string, district: string, months?: number): Promise<PriceTrendResponse> {
  const params = months ? `?months=${months}` : '';
  return api.get<PriceTrendResponse>(`/areas/${encodeURIComponent(city)}/${encodeURIComponent(district)}/trends${params}`);
}