"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api-client";

// ─── SharedShowcase type (backend SharedShowcaseItem ile uyumlu) ─

export interface SharedShowcase {
  id: string;
  title: string;
  slug: string;
  description?: string;
  agent_name: string;
  agent_phone?: string;
  property_count: number;
  views_count: number;
  office_name?: string;
  created_at: string;
}

// ─── Backend API Response ────────────────────────────────────────

interface SharedShowcaseListResponse {
  items: SharedShowcase[];
  total: number;
}

// ─── useSharedShowcases: Paylasim agi listesi ───────────────────

interface UseSharedShowcasesReturn {
  showcases: SharedShowcase[];
  isLoading: boolean;
  error: string | null;
}

export function useSharedShowcases(): UseSharedShowcasesReturn {
  const query = useQuery({
    queryKey: ["showcases-shared"],
    queryFn: async (): Promise<SharedShowcase[]> => {
      const response = await api.get<SharedShowcaseListResponse>("/showcases/shared");
      return response.items;
    },
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });

  return {
    showcases: query.data ?? [],
    isLoading: query.isLoading,
    error: query.error?.message ?? null,
  };
}
