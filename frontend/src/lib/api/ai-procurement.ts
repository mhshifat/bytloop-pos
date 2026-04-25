import { apiFetch } from "./fetcher";

export type InvoiceOcrRequest = {
  readonly asset: { readonly publicId: string; readonly url: string };
  readonly supplierHint?: string | null;
  readonly currency?: string | null;
};

export type InvoiceOcrLine = {
  readonly skuOrName: string;
  readonly quantity: number;
  readonly unitCostCents: number;
  readonly productId: string | null;
};

export type PurchaseOrderDraft = {
  readonly supplierId: string | null;
  readonly supplierName: string | null;
  readonly currency: string;
  readonly lines: readonly InvoiceOcrLine[];
};

export async function invoiceOcrToDraft(input: InvoiceOcrRequest): Promise<PurchaseOrderDraft> {
  return apiFetch<PurchaseOrderDraft>("/ai/procurement/invoice-ocr", { method: "POST", json: input });
}

