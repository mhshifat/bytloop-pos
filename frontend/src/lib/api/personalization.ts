import { apiFetch } from "./fetcher";

export type NextBestOfferItem = {
  readonly productId: string;
  readonly name: string;
  readonly sku: string;
  readonly priceCents: number;
  readonly currency: string;
  readonly score: number;
};

export async function nextBestOffers(input: {
  readonly productId: string;
  readonly limit?: number;
}): Promise<{ readonly productId: string; readonly items: readonly NextBestOfferItem[] }> {
  const sp = new URLSearchParams();
  sp.set("productId", input.productId);
  if (input.limit) sp.set("limit", String(input.limit));
  return apiFetch(`/personalization/next-best-offers?${sp.toString()}`);
}

