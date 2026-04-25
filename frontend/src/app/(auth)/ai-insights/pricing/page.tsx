import type { Metadata } from "next";
import Link from "next/link";

import { PricingInsightsPanel } from "@/components/modules/ai/pricing-insights-panel";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Pricing AI",
  path: "/ai-insights/pricing",
  noindex: true,
});

export default function PricingAiPage() {
  return (
    <section className="space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/ai-insights">← Back to AI insights</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Pricing & revenue optimization</h1>
        <p className="text-sm text-muted-foreground">
          Happy-hour suggestions, elasticity, bundle mining, dynamic rate hints, and jewelry rate suggestions.
        </p>
      </header>
      <PricingInsightsPanel />
    </section>
  );
}

