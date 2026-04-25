import type { Metadata } from "next";

import { ActivatePending } from "@/components/modules/identity/activate-pending";
import { getCurrentUser } from "@/lib/auth";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Activate account",
  path: "/activate-pending",
  noindex: true,
});

type ActivatePendingPageProps = {
  readonly searchParams: Promise<{ readonly email?: string }>;
};

export default async function ActivatePendingPage({ searchParams }: ActivatePendingPageProps) {
  const [{ email }, user] = await Promise.all([searchParams, getCurrentUser()]);
  const display = email ?? user?.email ?? "";

  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col justify-center p-6">
      <ActivatePending email={display} />
    </main>
  );
}
