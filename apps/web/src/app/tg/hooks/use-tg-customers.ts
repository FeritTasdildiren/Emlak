"use client";

import { useMutation, useQuery, useQueryClient, type UseMutateFunction } from "@tanstack/react-query";
import {
  fetchCustomers,
  createCustomer,
  updateCustomer,
  updateLeadStatus,
  humanizeError,
  type ApiCustomer,
  type CustomerCreateBody,
  type CustomerUpdateBody,
  type PaginatedResponse,
} from "@/app/tg/lib/tg-api";

// ================================================================
// Types
// ================================================================

export type LeadStatus = "cold" | "warm" | "hot" | "converted" | "lost";

export interface UseTgCustomersParams {
  page?: number;
  perPage?: number;
  search?: string;
  leadStatus?: LeadStatus | null;
}

// ================================================================
// List Hook
// ================================================================

/**
 * Müşteri listesi hook'u.
 * Arama, lead_status filtresi ve pagination destekler.
 */
export function useTgCustomers(params: UseTgCustomersParams = {}) {
  const { page = 1, perPage = 20, search, leadStatus } = params;

  const query = useQuery<PaginatedResponse<ApiCustomer>, Error>({
    queryKey: ["tg", "customers", { page, perPage, search, leadStatus }],
    queryFn: () =>
      fetchCustomers({
        page,
        per_page: perPage,
        search: search || undefined,
        lead_status: leadStatus || undefined,
      }),
    staleTime: 2 * 60 * 1000, // 2 dakika
    retry: 2,
  });

  return {
    customers: query.data?.items ?? [],
    total: query.data?.total ?? 0,
    isLoading: query.isLoading,
    isError: query.isError,
    error: query.error ? humanizeError(query.error) : null,
    refetch: query.refetch,
  };
}

// ================================================================
// Create Mutation
// ================================================================

export function useTgCreateCustomer() {
  const queryClient = useQueryClient();

  const mutation = useMutation<ApiCustomer, Error, CustomerCreateBody>({
    mutationFn: createCustomer,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tg", "customers"] });
      queryClient.invalidateQueries({ queryKey: ["tg", "dashboard"] });
    },
  });

  return {
    create: mutation.mutate as UseMutateFunction<ApiCustomer, Error, CustomerCreateBody>,
    createAsync: mutation.mutateAsync,
    isPending: mutation.isPending,
    isError: mutation.isError,
    isSuccess: mutation.isSuccess,
    error: mutation.error ? humanizeError(mutation.error) : null,
    reset: mutation.reset,
  };
}

// ================================================================
// Update Mutation
// ================================================================

export function useTgUpdateCustomer() {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    ApiCustomer,
    Error,
    { id: string; data: CustomerUpdateBody }
  >({
    mutationFn: ({ id, data }) => updateCustomer(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tg", "customers"] });
    },
  });

  return {
    update: mutation.mutate,
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error ? humanizeError(mutation.error) : null,
    reset: mutation.reset,
  };
}

// ================================================================
// Lead Status Mutation
// ================================================================

export function useTgUpdateLeadStatus() {
  const queryClient = useQueryClient();

  const mutation = useMutation<
    ApiCustomer,
    Error,
    { id: string; status: LeadStatus }
  >({
    mutationFn: ({ id, status }) => updateLeadStatus(id, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tg", "customers"] });
      queryClient.invalidateQueries({ queryKey: ["tg", "dashboard"] });
    },
  });

  return {
    updateStatus: mutation.mutate,
    isPending: mutation.isPending,
    isError: mutation.isError,
    error: mutation.error ? humanizeError(mutation.error) : null,
    reset: mutation.reset,
  };
}
