import type { Metadata } from "next";
import Link from "next/link";

import { SegmentsPanel } from "@/components/modules/customers/segments-panel";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Customer segments",
  path: "/customers/segments",
  noindex: true,
});

export default function CustomerSegmentsPage() {
  return (
    <section className="space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/customers">← Back to customers</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Customer segments</h1>
        <p className="text-sm text-muted-foreground">
          Auto-generated segments based on customer behavior. Recompute anytime.
        </p>
      </header>
      <SegmentsPanel />
    </section>
  );
}

