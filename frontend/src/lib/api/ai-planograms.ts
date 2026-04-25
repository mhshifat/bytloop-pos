import { apiFetch } from "./fetcher";

export type Planogram = {
  readonly id: string;
  readonly name: string;
  readonly locationName: string;
  readonly expectedSkus: readonly string[];
  readonly createdAt: string;
};

export async function listPlanograms(): Promise<readonly Planogram[]> {
  return apiFetch<readonly Planogram[]>("/ai/planograms");
}

export async function createPlanogram(input: {
  readonly name: string;
  readonly locationName?: string;
  readonly expectedSkus: readonly string[];
}): Promise<Planogram> {
  return apiFetch<Planogram>("/ai/planograms", { method: "POST", json: input });
}

export type PlanogramScanResult = {
  readonly scanId: string;
  readonly expectedSkus: readonly string[];
  readonly detectedSkus: readonly string[];
  readonly missingSkus: readonly string[];
  readonly unexpectedSkus: readonly string[];
};

export async function scanPlanogram(input: {
  readonly asset: { readonly publicId: string; readonly url: string };
  readonly planogramId?: string | null;
}): Promise<PlanogramScanResult> {
  return apiFetch<PlanogramScanResult>("/ai/planograms/scan", { method: "POST", json: input });
}

