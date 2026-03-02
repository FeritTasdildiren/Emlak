export interface Appointment {
  id: string;
  title: string;
  description?: string;
  appointment_date: string; // ISO 8601
  duration_minutes: number;
  status: "scheduled" | "completed" | "cancelled" | "no_show";
  location?: string;
  notes?: string;
  customer_id?: string;
  property_id?: string;
  user_id: string;
  user_name: string;
  customer_name?: string;
  property_title?: string;
  created_at: string;
  updated_at: string;
}

export interface AppointmentFormData {
  title: string;
  description?: string;
  appointment_date: string;
  duration_minutes: number;
  status: "scheduled" | "completed" | "cancelled" | "no_show";
  location?: string;
  notes?: string;
  customer_id?: string;
  property_id?: string;
}

export interface AppointmentListResponse {
  items: Appointment[];
  total: number;
  skip: number;
  limit: number;
}
