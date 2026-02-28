"use client";

import React, { useState } from 'react';

interface UpgradeBannerProps {
  featureName: string;
  requiredPlan: 'pro' | 'elite';
}

const PLAN_DETAILS: Record<string, { name: string; price: string; features: string[] }> = {
  pro: {
    name: 'Pro',
    price: '799 TL/ay',
    features: ['500 değerleme/ay', 'AI İlan Asistanı', 'Portal Export', 'Öncelikli destek'],
  },
  elite: {
    name: 'Elite',
    price: '1.499 TL/ay',
    features: ['Sınırsız değerleme', 'Virtual Staging', 'WhatsApp API', 'Özel entegrasyonlar'],
  },
};

export const UpgradeBanner: React.FC<UpgradeBannerProps> = ({ featureName, requiredPlan }) => {
  const [showDetails, setShowDetails] = useState(false);
  const plan = PLAN_DETAILS[requiredPlan];

  return (
    <div className="flex flex-col items-center justify-center p-8 bg-blue-50 border border-blue-200 rounded-lg text-center my-6">
      <div className="w-16 h-16 bg-blue-100 flex items-center justify-center rounded-full mb-4">
        <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="text-blue-600">
          <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
          <path d="M7 11V7a5 5 0 0 1 10 0v4" />
        </svg>
      </div>
      <h3 className="text-xl font-semibold text-gray-900 mb-2">{featureName} Özelliği</h3>
      <p className="text-gray-600 mb-6 max-w-md">
        Bu özellik sadece <strong>{plan.name}</strong> veya üzeri planlarda kullanılabilir.
      </p>
      <button
        className="px-6 py-2 bg-blue-600 text-white rounded-md font-medium hover:bg-blue-700 transition-colors"
        onClick={() => setShowDetails(!showDetails)}
      >
        {showDetails ? 'Gizle' : 'Plan Detayları'}
      </button>

      {showDetails && (
        <div className="mt-6 p-6 bg-white border border-blue-100 rounded-lg w-full max-w-sm text-left">
          <div className="flex items-center justify-between mb-4">
            <h4 className="text-lg font-bold text-gray-900">{plan.name} Plan</h4>
            <span className="text-lg font-semibold text-blue-600">{plan.price}</span>
          </div>
          <ul className="space-y-2 mb-4">
            {plan.features.map((f, i) => (
              <li key={i} className="flex items-center gap-2 text-sm text-gray-700">
                <svg className="w-4 h-4 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                {f}
              </li>
            ))}
          </ul>
          <p className="text-xs text-gray-500 text-center">
            Plan yükseltmek için <strong>destek@petqas.com</strong> adresine yazın.
          </p>
        </div>
      )}
    </div>
  );
};
