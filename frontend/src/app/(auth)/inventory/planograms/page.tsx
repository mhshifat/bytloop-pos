import type { Metadata } from "next";
import Link from "next/link";

import { PlanogramsPanel } from "@/components/modules/inventory/planograms-panel";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Planograms",
  path: "/inventory/planograms",
  noindex: true,
});

export default function PlanogramsPage() {
  return (
    <section className="mx-auto max-w-4xl space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/inventory">← Back to inventory</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Planograms</h1>
        <p className="text-sm text-muted-foreground">
          Define expected SKUs for a shelf, then scan a photo to detect missing/unexpected items.
        </p>
      </header>
      <PlanogramsPanel />
    </section>
  );
}

