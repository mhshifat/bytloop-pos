import type { Metadata } from "next";
import Link from "next/link";

import { RiskInsightsPanel } from "@/components/modules/ai/risk-insights-panel";
import { Button } from "@/components/shared/ui/button";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "Fraud & risk",
  path: "/ai-insights/risk",
  noindex: true,
});

export default function RiskAiPage() {
  return (
    <section className="space-y-6">
      <Button asChild variant="ghost" size="sm">
        <Link href="/ai-insights">← Back to AI insights</Link>
      </Button>
      <header>
        <h1 className="text-2xl font-semibold tracking-tight">Fraud & risk</h1>
        <p className="text-sm text-muted-foreground">
          Refund/void abuse flags, cash-drawer discrepancy patterns, and SoftPOS testing anomalies.
        </p>
      </header>
      <RiskInsightsPanel />
    </section>
  );
}

