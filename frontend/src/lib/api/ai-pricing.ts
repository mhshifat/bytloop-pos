import { apiFetch } from "./fetcher";

export type HappyHourSuggestion = {
  readonly startHour: number;
  readonly endHour: number;
  readonly percentOff: number;
  readonly reason: string;
};

export async function suggestHappyHour(params: { readonly days?: number } = {}): Promise<{
  readonly suggestions: readonly HappyHourSuggestion[];
}> {
  const sp = new URLSearchParams();
  if (params.days) sp.set("days", String(params.days));
  const q = sp.toString();
  return apiFetch(`/ai/pricing/happy-hour/suggest${q ? `?${q}` : ""}`);
}

export async function applyHappyHour(input: {
  readonly code: string;
  readonly name: string;
  readonly startHour: number;
  readonly endHour: number;
  readonly percentOff: number;
}): Promise<{ readonly ok: boolean; readonly discountId?: string; readonly code?: string }> {
  return apiFetch("/ai/pricing/happy-hour/apply", { method: "POST", json: input });
}

export async function getElasticity(params: { readonly days?: number; readonly limit?: number } = {}): Promise<{
  readonly items: readonly { readonly productId: string; readonly elasticity: number; readonly points: number }[];
}> {
  const sp = new URLSearchParams();
  if (params.days) sp.set("days", String(params.days));
  if (params.limit) sp.set("limit", String(params.limit));
  const q = sp.toString();
  return apiFetch(`/ai/pricing/elasticity${q ? `?${q}` : ""}`);
}

export async function suggestBundles(params: { readonly days?: number; readonly limit?: number } = {}): Promise<{
  readonly items: readonly { readonly a: string; readonly b: string; readonly cooccurrence: number; readonly lift: number }[];
}> {
  const sp = new URLSearchParams();
  if (params.days) sp.set("days", String(params.days));
  if (params.limit) sp.set("limit", String(params.limit));
  const q = sp.toString();
  return apiFetch(`/ai/pricing/bundles/suggest${q ? `?${q}` : ""}`);
}

export async function suggestDynamicPricing(): Promise<{
  readonly hotel: { readonly occupancyNext7d: number; readonly suggestedDeltaPct: number };
  readonly cinema: readonly { readonly showId: string; readonly title: string; readonly utilization: number; readonly suggestedDeltaPct: number }[];
  readonly rental: { readonly utilization: number; readonly suggestedDeltaPct: number };
}> {
  return apiFetch("/ai/pricing/dynamic/suggest");
}

export async function applyDynamicPricing(input: {
  readonly hotelDeltaPct?: number;
  readonly rentalDeltaPct?: number;
  readonly cinemaShowId?: string;
  readonly cinemaDeltaPct?: number;
}): Promise<{ readonly ok: boolean; readonly updated: number }> {
  return apiFetch("/ai/pricing/dynamic/apply", { method: "POST", json: input });
}

export async function suggestJewelryMetalRate(input: {
  readonly metal: string;
  readonly karat: number;
  readonly spotPerGramCents: number;
  readonly markupPct?: number;
}): Promise<{ readonly suggestedRatePerGramCents: number }> {
  return apiFetch("/ai/pricing/jewelry/metal-rate/suggest", { method: "POST", json: input });
}

export async function applyJewelryMetalRate(input: {
  readonly metal: string;
  readonly karat: number;
  readonly ratePerGramCents: number;
}): Promise<{ readonly ok: boolean; readonly id: string }> {
  return apiFetch("/ai/pricing/jewelry/metal-rate/apply", { method: "POST", json: input });
}

