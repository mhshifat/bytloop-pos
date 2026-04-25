import { apiFetch } from "./fetcher";

export async function getRefundVoidAbuse(params: { readonly days?: number } = {}): Promise<any> {
  const sp = new URLSearchParams();
  if (params.days) sp.set("days", String(params.days));
  const q = sp.toString();
  return apiFetch(`/ai/risk/refund-void-abuse${q ? `?${q}` : ""}`);
}

export async function getCashDrawerRisk(params: { readonly days?: number } = {}): Promise<any> {
  const sp = new URLSearchParams();
  if (params.days) sp.set("days", String(params.days));
  const q = sp.toString();
  return apiFetch(`/ai/risk/cash-drawer${q ? `?${q}` : ""}`);
}

export async function getSoftposAnomalies(params: { readonly minutes?: number } = {}): Promise<any> {
  const sp = new URLSearchParams();
  if (params.minutes) sp.set("minutes", String(params.minutes));
  const q = sp.toString();
  return apiFetch(`/ai/risk/softpos/anomalies${q ? `?${q}` : ""}`);
}

