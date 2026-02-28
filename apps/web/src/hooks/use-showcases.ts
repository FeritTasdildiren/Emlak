"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { Showcase } from "@/types/showcase";

// ─── Backend API Response Types ─────────────────────────────────

/** GET /showcases backend liste öğesi (özet) */
interface ShowcaseListItem {
  id: string;
  title: string;
  slug: string;
  is_active: boolean;
  views_count: number;
  created_at: string;
}

/** GET /showcases backend yanıtı */
interface ShowcaseListResponse {
  items: ShowcaseListItem[];
  total: number;
}

/** Tek vitrin detay/create/update yanıtı */
interface ShowcaseApiResponse {
  id: string;
  title: string;
  slug: string;
  description: string | null;
  selected_properties: string[];
  agent_phone: string | null;
  agent_email: string | null;
  agent_whatsapp: string | null;
  theme: string;
  is_active: boolean;
  views_count: number;
  created_at: string;
  updated_at: string;
}

/** Liste öğesini frontend Showcase tipine dönüştür */
function mapListItemToShowcase(item: ShowcaseListItem): Showcase {
  return {
    id: item.id,
    title: item.title,
    slug: item.slug,
    is_active: item.is_active,
    views_count: item.views_count,
    selected_properties: [], // Liste endpoint'inde yok, detayda var
    agent: { name: "" },
    theme: { primary_color: "#3b82f6", background: "light", layout: "grid" },
    created_at: item.created_at,
    updated_at: item.created_at,
  };
}

// ─── useShowcases: Vitrin listesi ───────────────────────────────

export function useShowcases() {
  const query = useQuery({
    queryKey: ["showcases"],
    queryFn: async (): Promise<Showcase[]> => {
      const response = await api.get<ShowcaseListResponse>("/showcases");
      return response.items.map(mapListItemToShowcase);
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

// ─── useShowcaseDetail: Tek vitrin detayı ───────────────────────

export function useShowcaseDetail(id: string | null) {
  return useQuery({
    queryKey: ["showcases", id],
    queryFn: async (): Promise<Showcase> => {
      const item = await api.get<ShowcaseApiResponse>(`/showcases/${id}`);
      return {
        id: item.id,
        title: item.title,
        slug: item.slug,
        description: item.description ?? undefined,
        is_active: item.is_active,
        views_count: item.views_count,
        selected_properties: item.selected_properties ?? [],
        agent: {
          name: "",
          phone: item.agent_phone ?? undefined,
          email: item.agent_email ?? undefined,
        },
        theme: { primary_color: "#3b82f6", background: "light", layout: "grid" },
        created_at: item.created_at,
        updated_at: item.updated_at,
      };
    },
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });
}

// ─── useCreateShowcase: Yeni vitrin oluşturma ───────────────────

export function useCreateShowcase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: {
      title: string;
      description?: string;
      selected_properties: string[];
      agent_phone?: string;
      agent_email?: string;
      agent_whatsapp?: string;
      theme?: string;
    }) => api.post<ShowcaseApiResponse>("/showcases", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["showcases"] });
    },
  });
}

// ─── useUpdateShowcase: Vitrin güncelleme ───────────────────────

export function useUpdateShowcase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Record<string, unknown> }) =>
      api.put<ShowcaseApiResponse>(`/showcases/${id}`, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["showcases"] });
      queryClient.invalidateQueries({ queryKey: ["showcases", variables.id] });
    },
  });
}

// ─── useDeleteShowcase: Vitrin silme ────────────────────────────

export function useDeleteShowcase() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/showcases/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["showcases"] });
    },
  });
}
