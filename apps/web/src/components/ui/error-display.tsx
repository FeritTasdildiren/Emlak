"use client";

import { AlertCircle, Check, Copy, RefreshCw } from "lucide-react";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { ApiError } from "@/lib/api-client";

interface ErrorDisplayProps {
  error: Error | ApiError | unknown;
  reset?: () => void;
  className?: string;
  title?: string;
}

interface UnknownError {
  requestId?: string;
  detail?: string;
  message?: string;
  [key: string]: unknown;
}

export function ErrorDisplay({
  error,
  reset,
  className,
  title = "Bir hata oluştu",
}: ErrorDisplayProps) {
  const [copied, setCopied] = useState(false);

  // Determine if it's an ApiError or has request_id property
  const isApiError = error instanceof ApiError;
  const requestId = isApiError ? error.requestId : (error as UnknownError)?.requestId;
  
  // Extract message
  const message =
    (error as UnknownError)?.detail ||
    (error as UnknownError)?.message ||
    "Beklenmedik bir hata meydana geldi.";

  const handleCopyRequestId = () => {
    if (requestId) {
      navigator.clipboard.writeText(requestId);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div
      className={cn(
        "rounded-lg border border-red-200 bg-red-50 p-4 text-red-900",
        className
      )}
      role="alert"
    >
      <div className="flex items-start gap-3">
        <AlertCircle className="mt-0.5 h-5 w-5 text-red-600 shrink-0" />
        <div className="flex-1 space-y-2">
          <h3 className="font-medium text-red-900">{title}</h3>
          
          <p className="text-sm text-red-800">{message}</p>

          {requestId && (
            <div className="flex items-center gap-2 mt-2">
              <code className="text-xs bg-red-100 px-2 py-1 rounded text-red-800 font-mono">
                Hata Kodu: REQ-{requestId.substring(0, 8)}...
              </code>
              <button
                onClick={handleCopyRequestId}
                className="p-1 hover:bg-red-200 rounded-md transition-colors text-red-700"
                title="Hata kodunu kopyala"
                type="button"
              >
                {copied ? (
                  <Check className="h-3.5 w-3.5" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}
                <span className="sr-only">Kopyala</span>
              </button>
            </div>
          )}

          {reset && (
            <button
              onClick={reset}
              className="mt-3 flex items-center gap-2 rounded-md bg-white px-3 py-1.5 text-sm font-medium text-red-900 shadow-sm ring-1 ring-inset ring-red-300 hover:bg-red-50 transition-colors"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              Tekrar Dene
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
