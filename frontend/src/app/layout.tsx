import type { Metadata } from "next";
import { NextIntlClientProvider } from "next-intl";
import { getLocale, getMessages } from "next-intl/server";
import type { ReactNode } from "react";

import { AppProviders } from "@/app/providers";
import { ErrorBoundary } from "@/components/shared/errors";
import { buildMetadata } from "@/lib/seo";

import "./globals.css";

export const metadata: Metadata = buildMetadata();

export default async function RootLayout({ children }: { readonly children: ReactNode }) {
  const locale = await getLocale();
  const messages = await getMessages();

  return (
    <html lang={locale} suppressHydrationWarning>
      <body>
        <NextIntlClientProvider locale={locale} messages={messages}>
          <AppProviders>
            <ErrorBoundary>{children}</ErrorBoundary>
          </AppProviders>
        </NextIntlClientProvider>
      </body>
    </html>
  );
}
