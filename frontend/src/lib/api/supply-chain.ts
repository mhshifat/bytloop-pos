import { apiFetch } from "./fetcher";

export type ReorderRecommendation = {
  readonly productId: string;
  readonly sku: string;
  readonly name: string;
  readonly locationId: string;
  readonly onHand: number;
  readonly currentReorderPoint: number;
  readonly recommendedReorderPoint: number;
  readonly leadTimeDays: number;
};

export async function getReorderRecommendations(params: {
  readonly locationId?: string;
  readonly days?: number;
  readonly limit?: number;
}): Promise<{ readonly items: readonly ReorderRecommendation[] }> {
  const sp = new URLSearchParams();
  if (params.locationId) sp.set("locationId", params.locationId);
  if (params.days) sp.set("days", String(params.days));
  if (params.limit) sp.set("limit", String(params.limit));
  const q = sp.toString();
  return apiFetch(`/ai/supply-chain/reorder-points${q ? `?${q}` : ""}`);
}

export async function applyReorderRecommendations(input: {
  readonly locationId: string;
  readonly items: readonly { readonly productId: string; readonly reorderPoint: number }[];
}): Promise<{ readonly ok: boolean; readonly updated?: number; readonly error?: string }> {
  return apiFetch("/ai/supply-chain/reorder-points/apply", { method: "POST", json: input });
}

export async function draftWeeklyPurchaseOrders(params: {
  readonly locationId?: string;
  readonly days?: number;
}): Promise<{
  readonly purchaseOrdersCreated: number;
  readonly purchaseOrders?: readonly { readonly id: string; readonly number: string; readonly supplierId: string }[];
}> {
  const sp = new URLSearchParams();
  if (params.locationId) sp.set("locationId", params.locationId);
  if (params.days) sp.set("days", String(params.days));
  const q = sp.toString();
  return apiFetch(`/ai/supply-chain/purchase-orders/draft-weekly${q ? `?${q}` : ""}`, {
    method: "POST",
    json: {},
  });
}

export type SupplierReliability = {
  readonly supplierId: string;
  readonly name: string;
  readonly onTimeRate: number;
  readonly poCount: number;
};

export async function getSupplierReliability(params: { readonly days?: number } = {}): Promise<{
  readonly items: readonly SupplierReliability[];
}> {
  const sp = new URLSearchParams();
  if (params.days) sp.set("days", String(params.days));
  const q = sp.toString();
  return apiFetch(`/ai/supply-chain/suppliers/reliability${q ? `?${q}` : ""}`);
}

