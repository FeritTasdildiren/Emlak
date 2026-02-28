import { PlanType, PlanFeatures } from '@/types/plan';

export const PLAN_CONFIGS: Record<PlanType, PlanFeatures> = {
  starter: {
    valuationMonthlyLimit: 50,
    crmContactLimit: 50,
    showcaseLimit: 1,
    hasAiAssistant: false,
    hasVirtualStaging: false,
    hasPortalExport: false,
    hasSharingNetwork: false,
  },
  pro: {
    valuationMonthlyLimit: 500,
    crmContactLimit: 500,
    showcaseLimit: 5,
    hasAiAssistant: true,
    hasVirtualStaging: false,
    hasPortalExport: true,
    hasSharingNetwork: true,
  },
  elite: {
    valuationMonthlyLimit: Infinity,
    crmContactLimit: Infinity,
    showcaseLimit: Infinity, // Or a high number
    hasAiAssistant: true,
    hasVirtualStaging: true,
    hasPortalExport: true,
    hasSharingNetwork: true,
  },
};

export type FeatureKey = keyof PlanFeatures;

/**
 * Belirli bir özelliğin kullanıcı planında aktif olup olmadığını kontrol eder.
 */
export const checkFeatureAccess = (planType: PlanType, featureKey: FeatureKey): boolean | number => {
  const config = PLAN_CONFIGS[planType];
  return config[featureKey];
};
