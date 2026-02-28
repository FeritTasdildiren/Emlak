"use client";

import { useMutation, useQueryClient, type UseMutateFunction } from "@tanstack/react-query";
import {
  submitValuation,
  humanizeError,
  ApiError,
  type ValuationRequest,
  type ValuationResponse,
} from "@/app/tg/lib/tg-api";

// ================================================================
// Types
// ================================================================

export interface TgValuationMutation {
  mutate: UseMutateFunction<ValuationResponse, Error, ValuationRequest>;
  data: ValuationResponse | null;
  isPending: boolean;
  isError: boolean;
  isSuccess: boolean;
  error: string | null;
  isQuotaExceeded: boolean;
  reset: () => void;
}

// ================================================================
// Hook
// ================================================================

/**
 * Değerleme mutation hook.
 * Form submit'te çağrılır, başarılı olunca dashboard cache'ini
 * invalidate eder (kota güncellenmeli).
 */
export function useTgValuation(): TgValuationMutation {
  const queryClient = useQueryClient();

  const mutation = useMutation<ValuationResponse, Error, ValuationRequest>({
    mutationFn: submitValuation,
    onSuccess: () => {
      // Kota değişti — dashboard'u yenile
      queryClient.invalidateQueries({ queryKey: ["tg", "dashboard"] });
    },
  });

  const isQuotaExceeded =
    mutation.error instanceof ApiError &&
    (mutation.error.status === 429 || mutation.error.status === 403);

  return {
    mutate: mutation.mutate,
    data: mutation.data ?? null,
    isPending: mutation.isPending,
    isError: mutation.isError,
    isSuccess: mutation.isSuccess,
    error: mutation.error ? humanizeError(mutation.error) : null,
    isQuotaExceeded,
    reset: mutation.reset,
  };
}
