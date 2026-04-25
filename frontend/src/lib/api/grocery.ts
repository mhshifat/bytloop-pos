import { apiFetch } from "./fetcher";

export type PluCode = {
  readonly id: string;
  readonly code: string;
  readonly productId: string;
};

export async function lookupPlu(code: string): Promise<{ productId: string }> {
  return apiFetch<{ productId: string }>(`/grocery/plu/${encodeURIComponent(code)}`);
}

export async function registerPlu(input: {
  readonly code: string;
  readonly productId: string;
}): Promise<PluCode> {
  return apiFetch<PluCode>("/grocery/plu", { method: "POST", json: input });
}

export type SellUnit = "each" | "kg" | "g" | "lb";

export type Weighable = {
  readonly productId: string;
  readonly sellUnit: SellUnit;
  readonly pricePerUnitCents: number;
  readonly tareGrams: number;
};

export async function upsertWeighable(input: {
  readonly productId: string;
  readonly sellUnit: SellUnit;
  readonly pricePerUnitCents: number;
  readonly tareGrams: number;
}): Promise<Weighable> {
  return apiFetch<Weighable>("/grocery/weighables", { method: "PUT", json: input });
}

export async function weigh(input: {
  readonly productId: string;
  readonly grams: number;
}): Promise<{ priceCents: number }> {
  return apiFetch<{ priceCents: number }>("/grocery/weigh", {
    method: "POST",
    json: input,
  });
}

export type ScanResult = {
  readonly productId: string;
  readonly lineTotalCents: number | null;
};

export async function scanInput(inputCode: string): Promise<ScanResult> {
  return apiFetch<ScanResult>("/grocery/scan", {
    method: "POST",
    json: { inputCode },
  });
}
