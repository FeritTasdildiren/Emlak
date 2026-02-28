"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { Customer } from "@/types/customer";
import type { Match } from "@/types/match";

// ─── Types ──────────────────────────────────────────────────────

/** Not tipi — frontend "general" kullanır, backend "note" döner */
export type NoteType = "general" | "call" | "meeting" | "email";

/** Müşteri notu — consumer'lar bu tipi kullanır */
export interface CustomerNote {
  id: string;
  customer_id: string;
  content: string;
  type: NoteType;
  author: string;
  created_at: string;
}

export interface UseCustomerDetailReturn {
  customer: Customer | null;
  notes: CustomerNote[];
  matches: Match[];
  isLoading: boolean;
  /** Not ekleme mutation'ı */
  addNote: (content: string, noteType: NoteType) => void;
  isAddingNote: boolean;
}

// ─── Backend Response Types ─────────────────────────────────────

interface ApiNoteResponse {
  id: string;
  content: string;
  note_type: string;
  user_id: string | null;
  created_at: string;
}

interface ApiNoteListResponse {
  items: ApiNoteResponse[];
  total: number;
}

interface ApiMatchResponse {
  id: string;
  property_id: string;
  customer_id: string;
  score: number;
  status: string;
  matched_at: string;
  responded_at: string | null;
  notes: string | null;
  created_at: string;
  updated_at: string;
}

interface ApiMatchListResponse {
  items: ApiMatchResponse[];
  total: number;
  page: number;
  per_page: number;
}

// ─── Backend → Frontend Mapping ─────────────────────────────────

/** Backend note_type → frontend NoteType mapping */
function mapNoteType(backendType: string): NoteType {
  if (backendType === "note") return "general";
  if (backendType === "call" || backendType === "meeting" || backendType === "email") {
    return backendType;
  }
  return "general";
}

/** Frontend NoteType → backend note_type mapping */
function toBackendNoteType(frontendType: NoteType): string {
  if (frontendType === "general") return "note";
  return frontendType;
}

function mapApiNote(note: ApiNoteResponse, customerId: string): CustomerNote {
  return {
    id: note.id,
    customer_id: customerId,
    content: note.content,
    type: mapNoteType(note.note_type),
    author: note.user_id ?? "Sistem",
    created_at: note.created_at,
  };
}

function mapApiMatch(match: ApiMatchResponse): Match {
  return {
    id: match.id,
    property_id: match.property_id,
    customer_id: match.customer_id,
    score: match.score, // Backend zaten 0-100
    status: match.status as Match["status"],
    matched_at: match.matched_at,
    responded_at: match.responded_at ?? undefined,
    notes: match.notes ?? "{}",
    // property alanı backend MatchResponse'da yok — MatchProperty opsiyonel
  };
}

// ─── React Query Keys ───────────────────────────────────────────

export const customerDetailKeys = {
  all: ["customer-detail"] as const,
  detail: (id: string) => [...customerDetailKeys.all, id] as const,
  notes: (id: string) => [...customerDetailKeys.all, id, "notes"] as const,
  matches: (id: string) => [...customerDetailKeys.all, id, "matches"] as const,
};

// ─── Hook ───────────────────────────────────────────────────────

/**
 * Müşteri detay hook'u — API entegrasyonu
 * GET /customers/{id} + GET /customers/{id}/notes + GET /matches?customer_id={id}
 */
export function useCustomerDetail(id: string): UseCustomerDetailReturn {
  const queryClient = useQueryClient();

  // Müşteri detayı
  const {
    data: customer,
    isLoading: isLoadingCustomer,
  } = useQuery({
    queryKey: customerDetailKeys.detail(id),
    queryFn: () => api.get<Customer>(`/customers/${id}`),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,     // 2 dakika
    gcTime: 5 * 60 * 1000,         // 5 dakika
  });

  // Müşteri notları
  const {
    data: notesData,
    isLoading: isLoadingNotes,
  } = useQuery({
    queryKey: customerDetailKeys.notes(id),
    queryFn: async () => {
      const response = await api.get<ApiNoteListResponse>(`/customers/${id}/notes`);
      return response.items
        .map((note) => mapApiNote(note, id))
        .sort(
          (a, b) =>
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
    },
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });

  // Müşteri eşleşmeleri
  const {
    data: matchesData,
    isLoading: isLoadingMatches,
  } = useQuery({
    queryKey: customerDetailKeys.matches(id),
    queryFn: async () => {
      const response = await api.get<ApiMatchListResponse>(
        `/matches?customer_id=${id}&per_page=50`
      );
      return response.items
        .map(mapApiMatch)
        .sort(
          (a, b) =>
            new Date(b.matched_at).getTime() - new Date(a.matched_at).getTime()
        );
    },
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });

  // Not ekleme mutation'ı
  const addNoteMutation = useMutation({
    mutationFn: async ({ content, noteType }: { content: string; noteType: NoteType }) => {
      return api.post<ApiNoteResponse>(`/customers/${id}/notes`, {
        content,
        note_type: toBackendNoteType(noteType),
      });
    },
    onSuccess: () => {
      // Not listesini yenile
      queryClient.invalidateQueries({ queryKey: customerDetailKeys.notes(id) });
    },
  });

  const addNote = (content: string, noteType: NoteType) => {
    addNoteMutation.mutate({ content, noteType });
  };

  return {
    customer: customer ?? null,
    notes: notesData ?? [],
    matches: matchesData ?? [],
    isLoading: isLoadingCustomer || isLoadingNotes || isLoadingMatches,
    addNote,
    isAddingNote: addNoteMutation.isPending,
  };
}
