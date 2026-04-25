import type { Metadata } from "next";
import Link from "next/link";

import { OpsInsightsPanel } from "@/components/modules/ai/ops-insights-panel";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Operations AI",
  path: "/ai-insights/ops",
  noindex: true,
});

export default function OpsAiPage() {
  return (
    <section className="space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/ai-insights">← Back to AI insights</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Operations & workforce</h1>
        <p className="text-sm text-muted-foreground">
          Staff scheduling, delivery routes, QSR prep-time estimates, table-turn hints, and stylist matching.
        </p>
      </header>
      <OpsInsightsPanel />
    </section>
  );
}

