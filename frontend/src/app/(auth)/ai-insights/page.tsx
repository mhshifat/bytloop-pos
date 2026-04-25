import type { Metadata } from "next";

import { AnomalyList } from "@/components/modules/ai/anomaly-list";
import { AttributionChart } from "@/components/modules/ai/attribution-chart";
import { BenchmarkCard } from "@/components/modules/ai/benchmark-card";
import { ChurnRiskList } from "@/components/modules/ai/churn-risk-list";
import { CohortHeatmap } from "@/components/modules/ai/cohort-heatmap";
import { ForecastChart } from "@/components/modules/ai/forecast-chart";
import { buildMetadata } from "@/lib/seo";

export const metadata: Metadata = buildMetadata({
  title: "AI insights",
  path: "/ai-insights",
  noindex: true,
});

export default function AiInsightsPage() {
  return (
    <section className="space-y-6">
      <header className="space-y-1.5">
        <h1 className="text-3xl font-semibold tracking-tight">AI insights</h1>
        <p className="text-sm text-muted-foreground">
          Forecasts, anomalies, churn risk, cohort retention, peer benchmarks,
          and marketing attribution — powered by ML + Groq.
        </p>
      </header>

      <ForecastChart />

      <div className="grid gap-4 md:grid-cols-2">
        <AnomalyList />
        <BenchmarkCard />
      </div>

      <CohortHeatmap />

      <ChurnRiskList />

      <AttributionChart />
    </section>
  );
}
