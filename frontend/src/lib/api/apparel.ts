import { apiFetch } from "./fetcher";

export type ApparelVariant = {
  readonly id: string;
  readonly productId: string;
  readonly sku: string;
  readonly barcode: string | null;
  readonly size: string;
  readonly color: string;
  readonly gender: string | null;
  readonly fit: string | null;
  readonly material: string | null;
  readonly priceCentsOverride: number | null;
  readonly stockQuantity: number;
};

export async function listVariants(productId: string): Promise<readonly ApparelVariant[]> {
  return apiFetch<readonly ApparelVariant[]>(`/apparel/products/${productId}/variants`);
}

export type GenerateMatrixInput = {
  readonly productId: string;
  readonly sizes: readonly string[];
  readonly colors: readonly string[];
  readonly skuPrefix: string;
};

export async function generateMatrix(
  input: GenerateMatrixInput,
): Promise<readonly ApparelVariant[]> {
  return apiFetch<readonly ApparelVariant[]>(
    "/apparel/variants/generate-matrix",
    { method: "POST", json: input },
  );
}

export async function lookupVariant(params: {
  readonly barcode?: string;
  readonly sku?: string;
}): Promise<ApparelVariant> {
  const sp = new URLSearchParams();
  if (params.barcode) sp.set("barcode", params.barcode);
  if (params.sku) sp.set("sku", params.sku);
  return apiFetch<ApparelVariant>(`/apparel/variants/lookup?${sp.toString()}`);
}

export async function updateVariant(
  variantId: string,
  input: {
    readonly barcode?: string | null;
    readonly gender?: string | null;
    readonly fit?: string | null;
    readonly material?: string | null;
    readonly priceCentsOverride?: number | null;
  },
): Promise<ApparelVariant> {
  return apiFetch<ApparelVariant>(`/apparel/variants/${variantId}`, {
    method: "PATCH",
    json: input,
  });
}

export async function adjustVariantStock(
  variantId: string,
  delta: number,
): Promise<ApparelVariant> {
  return apiFetch<ApparelVariant>(`/apparel/variants/${variantId}/stock-adjust`, {
    method: "POST",
    json: { delta },
  });
}
