export type CustomerType = "buyer" | "seller" | "renter" | "landlord";
export type LeadStatus = "cold" | "warm" | "hot" | "converted" | "lost";
export type MatchStatus = "pending" | "interested" | "passed" | "contacted" | "converted";

export interface Customer {
  id: string;
  full_name: string;
  phone?: string;
  email?: string;
  customer_type: CustomerType;
  budget_min?: number;
  budget_max?: number;
  desired_rooms?: string;
  desired_area_min?: number;
  desired_area_max?: number;
  desired_districts: string[];
  tags: string[];
  lead_status: LeadStatus;
  source?: string;
  notes?: string;
  last_contact_at?: string;
  created_at: string;
  updated_at: string;
}

export interface CustomerMatch {
  id: string;
  property_id: string;
  customer_id: string;
  score: number;
  status: MatchStatus;
  matched_at: string;
  responded_at?: string;
}
