'use client';

import { useState } from 'react';
import { PlanType, UserPlan } from '@/types/plan';
import { PLAN_CONFIGS, FeatureKey } from '@/lib/plan-features';

/**
 * Kullanıcı planını yöneten ve özelliklere erişim kontrolü sağlayan hook.
 */
export function usePlan() {
  // Gelecekte bir API'den veya global state'ten (AuthContext vb.) alınacak.
  // Varsayılan olarak 'pro' planını kullanıyoruz (Task gereksinimi).
  const [userPlan] = useState<UserPlan>({
    type: 'pro',
    features: PLAN_CONFIGS['pro'],
  });

  const checkAccess = (featureKey: FeatureKey): boolean | number => {
    return userPlan.features[featureKey];
  };

  const isAtLeast = (plan: PlanType): boolean => {
    const plans: PlanType[] = ['starter', 'pro', 'elite'];
    return plans.indexOf(userPlan.type) >= plans.indexOf(plan);
  };

  return {
    plan: userPlan.type,
    features: userPlan.features,
    checkAccess,
    isAtLeast,
    isPlan: (type: PlanType) => userPlan.type === type,
  };
}
