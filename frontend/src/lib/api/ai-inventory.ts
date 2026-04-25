import { apiFetch } from "./fetcher";

export type ShelfAuditRequest = {
  readonly asset: { readonly publicId: string; readonly url: string };
  readonly currency?: string | null;
};

export type ShelfLabelRow = {
  readonly skuOrName: string;
  readonly labelPriceCents: number;
  readonly currency: string;
};

export type ShelfMismatch = {
  readonly skuOrName: string;
  readonly labelPriceCents: number;
  readonly posPriceCents: number | null;
  readonly currency: string;
  readonly productId: string | null;
  readonly productName: string | null;
  readonly productSku: string | null;
};

export type ShelfAuditResponse = {
  readonly rows: readonly ShelfLabelRow[];
  readonly mismatches: readonly ShelfMismatch[];
};

export async function shelfLabelAudit(input: ShelfAuditRequest): Promise<ShelfAuditResponse> {
  return apiFetch<ShelfAuditResponse>("/ai/inventory/shelf-label-audit", { method: "POST", json: input });
}

