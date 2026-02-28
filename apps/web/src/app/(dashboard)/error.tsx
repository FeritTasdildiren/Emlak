'use client';

import { useEffect } from 'react';
import { ErrorDisplay } from '@/components/ui/error-display';

export default function DashboardError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="flex h-full min-h-[400px] flex-col items-center justify-center p-6">
      <div className="w-full max-w-lg">
        <ErrorDisplay 
          error={error} 
          reset={reset} 
          title="Yükleme Hatası"
          className="shadow-sm bg-white"
        />
      </div>
    </div>
  );
}
