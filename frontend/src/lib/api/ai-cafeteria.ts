import { apiFetch } from "./fetcher";

export type PlateScanRequest = {
  readonly asset: { readonly publicId: string; readonly url: string };
  readonly maxItems?: number;
};

export type PlateLineDraft = {
  readonly productId: string;
  readonly name: string;
  readonly quantity: number;
  readonly unitPriceCents: number;
  readonly currency: string;
};

export type PlateScanResponse = {
  readonly tags: readonly string[];
  readonly lines: readonly PlateLineDraft[];
};

export async function plateScan(input: PlateScanRequest): Promise<PlateScanResponse> {
  return apiFetch<PlateScanResponse>("/ai/cafeteria/plate-scan", { method: "POST", json: input });
}

