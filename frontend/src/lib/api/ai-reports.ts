import { apiFetch } from "./fetcher";

export type ForecastPoint = {
  readonly day: string;
  readonly forecastRevenueCents: number;
  readonly forecastUnits: number | null;
};

export type ForecastResult = {
  readonly horizonDays: number;
  readonly generatedAt: string;
  readonly productId: string | null;
  readonly points: readonly ForecastPoint[];
};

export type ForecastMethod = "seasonal_naive" | "prophet";

export async function getForecast(params: {
  readonly horizonDays?: number;
  readonly historyDays?: number;
  readonly productId?: string;
  readonly method?: ForecastMethod;
} = {}): Promise<ForecastResult> {
  const sp = new URLSearchParams();
  if (params.horizonDays) sp.set("horizonDays", String(params.horizonDays));
  if (params.historyDays) sp.set("historyDays", String(params.historyDays));
  if (params.productId) sp.set("productId", params.productId);
  if (params.method) sp.set("method", params.method);
  const q = sp.toString();
  return apiFetch<ForecastResult>(`/ai/reports/forecast${q ? `?${q}` : ""}`);
}

export type ForecastAccuracy = {
  readonly seasonal_naive: number | null;
  readonly prophet: number | null;
};

export async function getForecastAccuracy(params: {
  readonly holdoutDays?: number;
  readonly historyDays?: number;
} = {}): Promise<ForecastAccuracy> {
  const sp = new URLSearchParams();
  if (params.holdoutDays) sp.set("holdoutDays", String(params.holdoutDays));
  if (params.historyDays) sp.set("historyDays", String(params.historyDays));
  const q = sp.toString();
  return apiFetch<ForecastAccuracy>(
    `/ai/reports/forecast/accuracy${q ? `?${q}` : ""}`,
  );
}

export type AnomalyPoint = {
  readonly timestamp: string;
  readonly revenueCents: number;
  readonly severity: number;
  readonly note: string | null;
};

export type AnomalyReport = {
  readonly windowDays: number;
  readonly anomalies: readonly AnomalyPoint[];
};

export async function getAnomalies(windowDays = 60): Promise<AnomalyReport> {
  return apiFetch<AnomalyReport>(
    `/ai/reports/anomalies?windowDays=${windowDays}`,
  );
}

export type ChurnRiskCustomer = {
  readonly customerId: string;
  readonly email: string | null;
  readonly firstName: string;
  readonly lastName: string;
  readonly daysSinceLastOrder: number;
  readonly orderCount: number;
  readonly totalSpentCents: number;
  readonly churnProbability: number;
};

export type ChurnReport = {
  readonly threshold: number;
  readonly customers: readonly ChurnRiskCustomer[];
};

export async function getChurnRisk(threshold = 0.6): Promise<ChurnReport> {
  return apiFetch<ChurnReport>(`/ai/reports/churn-risk?threshold=${threshold}`);
}

export type LifetimeValuePrediction = {
  readonly customerId: string;
  readonly predicted12moCents: number;
  readonly past12moCents: number;
  readonly confidence: number;
};

export async function getLifetimeValue(
  customerId: string,
): Promise<LifetimeValuePrediction> {
  return apiFetch<LifetimeValuePrediction>(
    `/ai/reports/customers/${customerId}/ltv`,
  );
}

export type NLAnswer = {
  readonly question: string;
  readonly answer: string;
  readonly rows: readonly Record<string, unknown>[];
  readonly sql: string | null;
};

export async function askReporting(question: string): Promise<NLAnswer> {
  return apiFetch<NLAnswer>("/ai/reports/ask", {
    method: "POST",
    json: { question },
  });
}

export type CohortCell = {
  readonly cohortMonth: string;
  readonly monthsSinceAcquisition: number;
  readonly activeCustomers: number;
  readonly retentionPct: number;
};

export type CohortReport = {
  readonly cells: readonly CohortCell[];
  readonly insight: string | null;
};

export async function getCohortRetention(monthsBack = 12): Promise<CohortReport> {
  return apiFetch<CohortReport>(
    `/ai/reports/cohort-retention?monthsBack=${monthsBack}`,
  );
}

export type BenchmarkPoint = {
  readonly metric: string;
  readonly tenantValue: number;
  readonly peerMedian: number;
  readonly peerP25: number;
  readonly peerP75: number;
  readonly sampleSize: number;
};

export type BenchmarkReport = {
  readonly vertical: string;
  readonly points: readonly BenchmarkPoint[];
  readonly insight: string | null;
};

export async function getBenchmark(): Promise<BenchmarkReport> {
  return apiFetch<BenchmarkReport>("/ai/reports/benchmark");
}

export type AttributionChannel = {
  readonly channel: string;
  readonly attributedOrders: number;
  readonly attributedRevenueCents: number;
  readonly attributionWeight: number;
};

export type AttributionReport = {
  readonly windowDays: number;
  readonly channels: readonly AttributionChannel[];
};

export async function getAttribution(windowDays = 30): Promise<AttributionReport> {
  return apiFetch<AttributionReport>(
    `/ai/reports/attribution?windowDays=${windowDays}`,
  );
}
