import { apiFetch } from "./fetcher";

export type DiscountKind = "percent" | "fixed";

export type Discount = {
  readonly id: string;
  readonly code: string;
  readonly name: string;
  readonly kind: DiscountKind;
  readonly percent: string | null;
  readonly amountCents: number | null;
  readonly currency: string;
  readonly isActive: boolean;
};

export async function listDiscounts(): Promise<readonly Discount[]> {
  return apiFetch<readonly Discount[]>("/discounts");
}

export type DiscountCreate = {
  readonly code: string;
  readonly name: string;
  readonly kind: DiscountKind;
  readonly percent?: string | null;
  readonly amountCents?: number | null;
  readonly currency?: string;
};

export async function createDiscount(input: DiscountCreate): Promise<Discount> {
  return apiFetch<Discount>("/discounts", { method: "POST", json: input });
}
