import { apiFetch } from "./fetcher";

export type ProductSupplier = {
  readonly id: string;
  readonly productId: string;
  readonly supplierId: string;
  readonly isPreferred: boolean;
  readonly unitCostCents: number;
  readonly leadTimeDays: number;
  readonly leadTimeStdDays: number;
  readonly minOrderQty: number;
  readonly packSize: number;
};

export async function listProductSuppliers(params: {
  readonly productId?: string;
  readonly supplierId?: string;
} = {}): Promise<readonly ProductSupplier[]> {
  const sp = new URLSearchParams();
  if (params.productId) sp.set("productId", params.productId);
  if (params.supplierId) sp.set("supplierId", params.supplierId);
  const q = sp.toString();
  return apiFetch(`/product-suppliers${q ? `?${q}` : ""}`);
}

export async function upsertProductSupplier(input: {
  readonly productId: string;
  readonly supplierId: string;
  readonly isPreferred: boolean;
  readonly unitCostCents: number;
  readonly leadTimeDays: number;
  readonly leadTimeStdDays: number;
  readonly minOrderQty: number;
  readonly packSize: number;
}): Promise<ProductSupplier> {
  return apiFetch("/product-suppliers", { method: "POST", json: input });
}

export async function deleteProductSupplier(input: {
  readonly productId: string;
  readonly supplierId: string;
}): Promise<{ readonly ok: boolean }> {
  const sp = new URLSearchParams();
  sp.set("productId", input.productId);
  sp.set("supplierId", input.supplierId);
  return apiFetch(`/product-suppliers?${sp.toString()}`, { method: "DELETE" });
}

