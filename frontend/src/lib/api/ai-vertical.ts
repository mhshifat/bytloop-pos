import { apiFetch } from "./fetcher";

export async function getMenuEngineering(params: { readonly days?: number } = {}): Promise<any> {
  const sp = new URLSearchParams();
  if (params.days) sp.set("days", String(params.days));
  const q = sp.toString();
  return apiFetch(`/ai/vertical/menu-engineering${q ? `?${q}` : ""}`);
}

export async function getRestaurantWaitTime(params: { readonly station?: string } = {}): Promise<any> {
  const sp = new URLSearchParams();
  if (params.station) sp.set("station", params.station);
  const q = sp.toString();
  return apiFetch(`/ai/vertical/restaurant/wait-time${q ? `?${q}` : ""}`);
}

export async function getCannabisPotencyPriceMatch(params: {
  readonly desiredThcPct?: number;
  readonly desiredCbdPct?: number;
  readonly maxPriceCents?: number;
  readonly limit?: number;
} = {}): Promise<any> {
  const sp = new URLSearchParams();
  if (params.desiredThcPct != null) sp.set("desiredThcPct", String(params.desiredThcPct));
  if (params.desiredCbdPct != null) sp.set("desiredCbdPct", String(params.desiredCbdPct));
  if (params.maxPriceCents != null) sp.set("maxPriceCents", String(params.maxPriceCents));
  if (params.limit != null) sp.set("limit", String(params.limit));
  const q = sp.toString();
  return apiFetch(`/ai/vertical/cannabis/potency-price-match${q ? `?${q}` : ""}`);
}

export async function getHotelUpsell(params: { readonly forDate?: string; readonly limit?: number } = {}): Promise<any> {
  const sp = new URLSearchParams();
  if (params.forDate) sp.set("forDate", params.forDate);
  if (params.limit != null) sp.set("limit", String(params.limit));
  const q = sp.toString();
  return apiFetch(`/ai/vertical/hotel/upsell${q ? `?${q}` : ""}`);
}

export async function getRentalDamageRisk(params: { readonly limit?: number } = {}): Promise<any> {
  const sp = new URLSearchParams();
  if (params.limit != null) sp.set("limit", String(params.limit));
  const q = sp.toString();
  return apiFetch(`/ai/vertical/rental/damage-risk${q ? `?${q}` : ""}`);
}

export async function getGymChurnNudges(params: { readonly days?: number; readonly limit?: number } = {}): Promise<any> {
  const sp = new URLSearchParams();
  if (params.days) sp.set("days", String(params.days));
  if (params.limit != null) sp.set("limit", String(params.limit));
  const q = sp.toString();
  return apiFetch(`/ai/vertical/gym/churn-nudges${q ? `?${q}` : ""}`);
}

