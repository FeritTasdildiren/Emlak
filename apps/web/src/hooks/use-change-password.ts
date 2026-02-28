"use client";

import { useMutation } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api-client";
import type { ChangePasswordRequest } from "@/types/settings";

/**
 * Şifre değiştirme mutation hook'u.
 * POST /auth/change-password endpoint'ini kullanır.
 * Rate limit: 5/saat
 */
export function useChangePassword() {
  const mutation = useMutation<void, ApiError, ChangePasswordRequest>({
    mutationFn: (data) =>
      api.post<void>("/auth/change-password", data),
  });

  return {
    changePassword: mutation.mutate,
    changePasswordAsync: mutation.mutateAsync,
    isPending: mutation.isPending,
    isSuccess: mutation.isSuccess,
    isError: mutation.isError,
    error: mutation.error,
    reset: mutation.reset,
  };
}
