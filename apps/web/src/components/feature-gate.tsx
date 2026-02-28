'use client';

import React, { ReactNode } from 'react';
import { usePlan } from '@/hooks/use-plan';
import { FeatureKey } from '@/lib/plan-features';
import { UpgradeBanner } from '@/components/upgrade-banner';

interface FeatureGateProps {
  feature: FeatureKey;
  children: ReactNode;
  fallback?: ReactNode;
  featureName?: string;
  requiredPlan?: 'pro' | 'elite';
}

/**
 * Belirli bir özelliğin kullanıcı planında aktif olup olmadığını kontrol eden wrapper bileşeni.
 * Eğer özellik kapalıysa, bir fallback içeriği (varsayılan: UpgradeBanner) döner.
 */
export function FeatureGate({ 
  feature, 
  children, 
  fallback,
  featureName = 'Bu Özellik',
  requiredPlan = 'pro'
}: FeatureGateProps) {
  const { checkAccess } = usePlan();
  
  const hasAccess = checkAccess(feature);

  if (hasAccess === true) {
    return <>{children}</>;
  }

  // Sayısal değerler için (limitler), sadece boolean özellikleri feature-gate ile yönetiyoruz.
  if (typeof hasAccess === 'number') {
    return <>{children}</>;
  }

  if (fallback) {
    return <>{fallback}</>;
  }

  return <UpgradeBanner featureName={featureName} requiredPlan={requiredPlan} />;
}
