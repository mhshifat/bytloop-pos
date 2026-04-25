import { apiFetch } from "./fetcher";

export type QuantityBreak = {
  readonly id: string;
  readonly productId: string;
  readonly minQuantity: number;
  readonly unitPriceCents: number;
};

export type QuantityBreakTier = {
  readonly minQuantity: number;
  readonly unitPriceCents: number;
};

export type ResolvedPrice = {
  readonly productId: string;
  readonly quantity: number;
  readonly unitPriceCents: number;
  readonly matchedMinQuantity: number | null;
};

export async function listQuantityBreaks(
  productId: string,
): Promise<readonly QuantityBreak[]> {
  return apiFetch<readonly QuantityBreak[]>(
    `/hardware/quantity-breaks?productId=${encodeURIComponent(productId)}`,
  );
}

export async function setQuantityBreaks(input: {
  readonly productId: string;
  readonly tiers: readonly QuantityBreakTier[];
}): Promise<readonly QuantityBreak[]> {
  return apiFetch<readonly QuantityBreak[]>("/hardware/quantity-breaks", {
    method: "PUT",
    json: input,
  });
}

export async function resolveUnitPrice(input: {
  readonly productId: string;
  readonly quantity: number;
}): Promise<ResolvedPrice> {
  return apiFetch<ResolvedPrice>("/hardware/quantity-breaks/resolve", {
    method: "POST",
    json: input,
  });
}
