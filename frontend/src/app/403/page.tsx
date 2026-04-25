import type { Metadata } from "next";
import Link from "next/link";

import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Access denied",
  path: "/403",
  noindex: true,
});

export default function ForbiddenPage() {
  return (
    <main className="mx-auto flex min-h-dvh max-w-md flex-col items-center justify-center gap-4 p-6 text-center">
      <h1 className="text-3xl font-semibold">Access denied</h1>
      <p className="text-sm text-muted-foreground">
        You don&apos;t have permission to view that page. If you think this is a mistake,
        ask an admin to adjust your role.
      </p>
      <Button asChild>
        <Link href="/dashboard">Back to dashboard</Link>
      </Button>
    </main>
  );
}
