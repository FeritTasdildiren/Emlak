export type PlanType = 'starter' | 'pro' | 'elite';

export interface PlanFeatures {
  valuationMonthlyLimit: number;
  crmContactLimit: number;
  showcaseLimit: number;
  hasAiAssistant: boolean;
  hasVirtualStaging: boolean;
  hasPortalExport: boolean;
  hasSharingNetwork: boolean;
}

export interface UserPlan {
  type: PlanType;
  features: PlanFeatures;
  expiresAt?: string;
}
