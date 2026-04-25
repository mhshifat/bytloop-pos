"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useEffect, useState } from "react";
import { Toaster } from "sonner";

import { AuthSessionSync } from "@/components/shared/auth-session-sync";
import { InstallPrompt } from "@/components/shared/install-prompt";
import { showErrorToast } from "@/components/shared/errors";
import { ThemeProvider } from "@/components/shared/layout/theme-provider";
import { isApiError } from "@/lib/api/error";
import { registerServiceWorker } from "@/lib/offline/service-worker";
import { startOfflineSync } from "@/lib/offline/sync";
import { initTracker } from "@/lib/tracker";

export function AppProviders({ children }: { readonly children: React.ReactNode }) {
  useEffect(() => {
    initTracker();
    void registerServiceWorker();
    const stop = startOfflineSync();
    return () => stop();
  }, []);

  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            retry: (failureCount, error) => {
              if (isApiError(error)) {
                // Don't retry 4xx client errors.
                if (error.status >= 400 && error.status < 500) return false;
              }
              return failureCount < 2;
            },
            staleTime: 30_000,
          },
          mutations: {
            onError: (error) => {
              if (isApiError(error)) showErrorToast(error);
            },
          },
        },
      }),
  );

  return (
    <ThemeProvider>
      <QueryClientProvider client={client}>
        <AuthSessionSync />
        {children}
        <InstallPrompt />
        <Toaster position="top-right" richColors closeButton />
        {process.env.NODE_ENV === "development" ? <ReactQueryDevtools /> : null}
      </QueryClientProvider>
    </ThemeProvider>
  );
}
