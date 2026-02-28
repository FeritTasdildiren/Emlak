'use client';

import { useEffect } from 'react';
import { ErrorDisplay } from '@/components/ui/error-display';

export default function Error({
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
    <div className="flex min-h-[50vh] flex-col items-center justify-center p-4">
      <ErrorDisplay 
        error={error} 
        reset={reset} 
        title="Bir şeyler ters gitti"
        className="w-full max-w-md shadow-md"
      />
    </div>
  );
}
