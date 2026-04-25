import type { Metadata } from "next";
import Link from "next/link";

import { VerticalInsightsPanel } from "@/components/modules/ai/vertical-insights-panel";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Vertical AI",
  path: "/ai-insights/vertical",
  noindex: true,
});

export default function VerticalAiPage() {
  return (
    <section className="space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/ai-insights">← Back to AI insights</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Vertical AI</h1>
        <p className="text-sm text-muted-foreground">
          Menu engineering, restaurant wait-time ETA, cannabis matching, hotel upsell scoring, rental risk, and gym churn nudges.
        </p>
      </header>
      <VerticalInsightsPanel />
    </section>
  );
}

