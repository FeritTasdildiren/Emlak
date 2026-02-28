"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api-client";
import type { Customer, CustomerType, LeadStatus } from "@/types/customer";

// ─── API Response Types ──────────────────────────────────────────

interface CustomerListResponse {
  items: Customer[];
  total: number;
  page: number;
  per_page: number;
}

interface NoteResponse {
  id: string;
  content: string;
  created_at: string;
  created_by?: string;
}

interface NoteListResponse {
  items: NoteResponse[];
  total: number;
}

// ─── Hook Params & Return Types ──────────────────────────────────

export interface UseCustomersParams {
  search: string;
  leadStatus: LeadStatus | null;
  customerType: CustomerType | null;
  page: number;
  perPage: number;
}

export type PipelineCounts = Record<LeadStatus, number>;

// ─── useCustomers: Ana liste hook'u ─────────────────────────────

export function useCustomers(params: UseCustomersParams) {
  const { search, leadStatus, customerType, page, perPage } = params;

  // Ana liste sorgusu (lead_status filtreli)
  const listQuery = useQuery({
    queryKey: ["customers", { search, leadStatus, customerType, page, perPage }],
    queryFn: async (): Promise<CustomerListResponse> => {
      const searchParams = new URLSearchParams();
      searchParams.set("page", String(page));
      searchParams.set("per_page", String(perPage));
      if (search) searchParams.set("search", search);
      if (leadStatus) searchParams.set("lead_status", leadStatus);
      if (customerType) searchParams.set("customer_type", customerType);

      const qs = searchParams.toString();
      return api.get<CustomerListResponse>(`/customers${qs ? `?${qs}` : ""}`);
    },
    staleTime: 2 * 60 * 1000, // 2dk
    gcTime: 5 * 60 * 1000,    // 5dk
  });

  // Pipeline sayıları: lead_status filtresi OLMADAN, ama search + customerType ile
  // Her lead_status için ayrı count sorgusu (per_page=1 ile sadece total alıyoruz)
  const pipelineQuery = useQuery({
    queryKey: ["customers-pipeline", { search, customerType }],
    queryFn: async (): Promise<PipelineCounts> => {
      const counts: PipelineCounts = { cold: 0, warm: 0, hot: 0, converted: 0, lost: 0 };
      const statuses: LeadStatus[] = ["cold", "warm", "hot", "converted", "lost"];

      const promises = statuses.map(async (status) => {
        const sp = new URLSearchParams();
        sp.set("page", "1");
        sp.set("per_page", "1");
        sp.set("lead_status", status);
        if (search) sp.set("search", search);
        if (customerType) sp.set("customer_type", customerType);

        const res = await api.get<CustomerListResponse>(`/customers?${sp.toString()}`);
        counts[status] = res.total;
      });

      await Promise.all(promises);
      return counts;
    },
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });

  return {
    customers: listQuery.data?.items ?? [],
    total: listQuery.data?.total ?? 0,
    pipelineCounts: pipelineQuery.data ?? { cold: 0, warm: 0, hot: 0, converted: 0, lost: 0 },
    isLoading: listQuery.isLoading,
    isError: listQuery.isError,
    error: listQuery.error,
  };
}

// ─── useCustomerDetail: Tek müşteri detayı ──────────────────────

export function useCustomerDetail(id: string | null) {
  return useQuery({
    queryKey: ["customers", id],
    queryFn: () => api.get<Customer>(`/customers/${id}`),
    enabled: !!id,
    staleTime: 2 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });
}

// ─── useCustomerNotes: Müşteri notları ──────────────────────────

export function useCustomerNotes(customerId: string | null) {
  return useQuery({
    queryKey: ["customers", customerId, "notes"],
    queryFn: () => api.get<NoteListResponse>(`/customers/${customerId}/notes`),
    enabled: !!customerId,
    staleTime: 1 * 60 * 1000,
    gcTime: 5 * 60 * 1000,
  });
}

// ─── useCreateCustomer: Yeni müşteri oluşturma ──────────────────

export function useCreateCustomer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: Partial<Customer>) => api.post<Customer>("/customers", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["customers-pipeline"] });
    },
  });
}

// ─── useUpdateCustomer: Müşteri güncelleme ──────────────────────

export function useUpdateCustomer() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Customer> }) =>
      api.patch<Customer>(`/customers/${id}`, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["customers-pipeline"] });
      queryClient.invalidateQueries({ queryKey: ["customers", variables.id] });
    },
  });
}

// ─── useUpdateLeadStatus: Lead status güncelleme ────────────────

export function useUpdateLeadStatus() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, status }: { id: string; status: LeadStatus }) =>
      api.patch<Customer>(`/customers/${id}/status`, { status }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["customers"] });
      queryClient.invalidateQueries({ queryKey: ["customers-pipeline"] });
      queryClient.invalidateQueries({ queryKey: ["customers", variables.id] });
    },
  });
}

// ─── useAddCustomerNote: Not ekleme ─────────────────────────────

export function useAddCustomerNote() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ customerId, content }: { customerId: string; content: string }) =>
      api.post<NoteResponse>(`/customers/${customerId}/notes`, { content }),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["customers", variables.customerId, "notes"] });
      queryClient.invalidateQueries({ queryKey: ["customers", variables.customerId] });
    },
  });
}
