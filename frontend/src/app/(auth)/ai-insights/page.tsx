import type { Metadata } from "next";

import { AiStatusBadge } from "@/components/modules/ai/ai-status-badge";
import { AnomalyList } from "@/components/modules/ai/anomaly-list";
import { AskReportingPanel } from "@/components/modules/ai/ask-reporting-panel";
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
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h1 className="text-3xl font-semibold tracking-tight">AI insights</h1>
          <AiStatusBadge />
        </div>
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

      <div className="grid gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-border bg-surface p-4">
          <AskReportingPanel />
        </div>
        <div className="rounded-lg border border-border bg-surface p-4">
          <p className="text-sm font-medium">Tip</p>
          <p className="mt-2 text-sm text-muted-foreground">
            If AI is disabled, ask/report endpoints will return a safe fallback.
            Enable Groq on the backend with <span className="font-mono">AI_PROVIDER=groq</span>{" "}
            and <span className="font-mono">AI_GROQ_API_KEY</span>.
          </p>
        </div>
      </div>
    </section>
  );
}
