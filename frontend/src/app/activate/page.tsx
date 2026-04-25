import type { Metadata } from "next";

import { ActivateClient } from "./activate-client";

import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Activate account",
  path: "/activate",
  noindex: true,
});

type ActivatePageProps = {
  readonly searchParams: Promise<{ readonly token?: string }>;
};

export default async function ActivatePage({ searchParams }: ActivatePageProps) {
  const { token } = await searchParams;
  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center p-6 text-center">
      {token ? (
        <ActivateClient token={token} />
      ) : (
        <>
          <h1 className="text-2xl font-semibold">Missing activation link</h1>
          <p className="mt-2 text-sm text-[var(--color-muted)]">
            Open the link from your email to activate your account.
          </p>
        </>
      )}
    </main>
  );
}
