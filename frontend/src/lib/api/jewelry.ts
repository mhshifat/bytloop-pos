import { apiFetch } from "./fetcher";

export type JewelryAttribute = {
  readonly productId: string;
  readonly metal: string;
  readonly karat: number;
  readonly grossGrams: string;
  readonly netGrams: string;
  readonly makingChargePct: string;
  readonly makingChargePerGramCents: number;
  readonly wastagePct: string;
  readonly stoneValueCents: number;
  readonly certificateNo: string | null;
};

export async function getAttributes(productId: string): Promise<JewelryAttribute> {
  return apiFetch<JewelryAttribute>(`/jewelry/products/${productId}`);
}

export async function upsertAttributes(
  productId: string,
  input: {
    readonly metal: string;
    readonly karat: number;
    readonly grossGrams: string;
    readonly netGrams: string;
    readonly makingChargePct: string;
    readonly makingChargePerGramCents: number;
    readonly wastagePct: string;
    readonly stoneValueCents: number;
    readonly certificateNo?: string | null;
  },
): Promise<JewelryAttribute> {
  return apiFetch<JewelryAttribute>(`/jewelry/products/${productId}`, {
    method: "PUT",
    json: { productId, ...input },
  });
}

export type MetalRate = {
  readonly id: string;
  readonly metal: string;
  readonly karat: number;
  readonly ratePerGramCents: number;
  readonly effectiveOn: string;
};

export async function listRates(): Promise<readonly MetalRate[]> {
  return apiFetch<readonly MetalRate[]>("/jewelry/rates");
}

export async function upsertRate(input: {
  readonly metal: string;
  readonly karat: number;
  readonly ratePerGramCents: number;
  readonly effectiveOn: string;
}): Promise<MetalRate> {
  return apiFetch<MetalRate>("/jewelry/rates", { method: "PUT", json: input });
}

export type JewelryQuote = {
  readonly productId: string;
  readonly metalValueCents: number;
  readonly wastageCents: number;
  readonly makingChargeCents: number;
  readonly stoneValueCents: number;
  readonly totalCents: number;
};

export async function getQuote(productId: string): Promise<JewelryQuote> {
  return apiFetch<JewelryQuote>(`/jewelry/products/${productId}/quote`);
}
