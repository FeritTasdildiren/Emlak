"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api, ApiError } from "@/lib/api-client";
import { 
  Appointment, 
  AppointmentFormData, 
  AppointmentListResponse 
} from "@/types/appointment";

/**
 * Dashboard için yaklaşan randevuları getiren hook.
 * GET /appointments/upcoming?limit=5
 */
export function useUpcomingAppointments(limit = 5) {
  return useQuery<Appointment[], ApiError>({
    queryKey: ["appointments", "upcoming", limit],
    queryFn: () => api.get<Appointment[]>(`/appointments/upcoming?limit=${limit}`),
    staleTime: 2 * 60 * 1000, // 2 dakika
    gcTime: 5 * 60 * 1000,    // 5 dakika
  });
}

interface UseAppointmentsParams {
  skip?: number;
  limit?: number;
  status?: string;
  date_from?: string;
  date_to?: string;
}

/**
 * Randevu listesini getiren hook.
 * GET /appointments?skip&limit&status&date_from&date_to
 */
export function useAppointments(params: UseAppointmentsParams = {}) {
  const queryParams = new URLSearchParams();
  if (params.skip !== undefined) queryParams.append("skip", params.skip.toString());
  if (params.limit !== undefined) queryParams.append("limit", params.limit.toString());
  if (params.status) queryParams.append("status", params.status);
  if (params.date_from) queryParams.append("date_from", params.date_from);
  if (params.date_to) queryParams.append("date_to", params.date_to);

  const queryString = queryParams.toString();
  const url = `/appointments${queryString ? `?${queryString}` : ""}`;

  return useQuery<AppointmentListResponse, ApiError>({
    queryKey: ["appointments", "list", params],
    queryFn: () => api.get<AppointmentListResponse>(url),
    staleTime: 1 * 60 * 1000, // 1 dakika
    gcTime: 5 * 60 * 1000,    // 5 dakika
  });
}

/**
 * Yeni randevu oluşturan mutation hook.
 * POST /appointments
 */
export function useCreateAppointment() {
  const queryClient = useQueryClient();

  return useMutation<Appointment, ApiError, AppointmentFormData>({
    mutationFn: (data) => api.post<Appointment>("/appointments", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

/**
 * Randevu güncelleyen mutation hook.
 * PATCH /appointments/{id}
 */
export function useUpdateAppointment(id: string) {
  const queryClient = useQueryClient();

  return useMutation<Appointment, ApiError, Partial<AppointmentFormData>>({
    mutationFn: (data) => api.patch<Appointment>(`/appointments/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}

/**
 * Randevu silen mutation hook.
 * DELETE /appointments/{id}
 */
export function useDeleteAppointment() {
  const queryClient = useQueryClient();

  return useMutation<void, ApiError, string>({
    mutationFn: (id) => api.delete<void>(`/appointments/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["appointments"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    },
  });
}
