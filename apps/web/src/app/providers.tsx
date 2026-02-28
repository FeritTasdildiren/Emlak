"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, ReactNode } from "react";
import { WebSocketProvider } from "@/providers/websocket-provider";

export default function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 5 * 60 * 1000,   // 5 dakika
            gcTime: 10 * 60 * 1000,      // 10 dakika (gcTime >= staleTime ZORUNLU)
            refetchOnWindowFocus: true,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <WebSocketProvider>
        {children}
      </WebSocketProvider>
    </QueryClientProvider>
  );
}
