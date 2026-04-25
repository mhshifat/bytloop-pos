import { apiFetch } from "./fetcher";

export type VirtualBrand = {
  readonly id: string;
  readonly code: string;
  readonly name: string;
  readonly logoUrl: string | null;
  readonly isActive: boolean;
  readonly createdAt: string;
};

export type BrandProduct = {
  readonly brandId: string;
  readonly productId: string;
  readonly createdAt: string;
};

export type BrandOrder = {
  readonly id: string;
  readonly orderId: string;
  readonly brandId: string;
  readonly externalOrderRef: string | null;
  readonly createdAt: string;
};

export type CreateBrandInput = {
  readonly code: string;
  readonly name: string;
  readonly logoUrl?: string | null;
  readonly isActive?: boolean;
};

export type UpdateBrandInput = {
  readonly name?: string;
  readonly logoUrl?: string | null;
  readonly isActive?: boolean;
};

export async function createBrand(input: CreateBrandInput): Promise<VirtualBrand> {
  return apiFetch<VirtualBrand>("/cloud-kitchen/brands", {
    method: "POST",
    json: input,
  });
}

export async function listBrands(
  includeInactive = false,
): Promise<readonly VirtualBrand[]> {
  const qs = includeInactive ? "?includeInactive=true" : "";
  return apiFetch<readonly VirtualBrand[]>(`/cloud-kitchen/brands${qs}`);
}

export async function getBrand(brandId: string): Promise<VirtualBrand> {
  return apiFetch<VirtualBrand>(`/cloud-kitchen/brands/${brandId}`);
}

export async function updateBrand(
  brandId: string,
  input: UpdateBrandInput,
): Promise<VirtualBrand> {
  return apiFetch<VirtualBrand>(`/cloud-kitchen/brands/${brandId}`, {
    method: "PATCH",
    json: input,
  });
}

export async function attachProduct(
  brandId: string,
  productId: string,
): Promise<BrandProduct> {
  return apiFetch<BrandProduct>(`/cloud-kitchen/brands/${brandId}/products`, {
    method: "POST",
    json: { productId },
  });
}

export async function detachProduct(
  brandId: string,
  productId: string,
): Promise<void> {
  await apiFetch<void>(
    `/cloud-kitchen/brands/${brandId}/products/${productId}`,
    { method: "DELETE" },
  );
}

export async function listBrandProducts(
  brandId: string,
): Promise<readonly BrandProduct[]> {
  return apiFetch<readonly BrandProduct[]>(
    `/cloud-kitchen/brands/${brandId}/products`,
  );
}

export type RecordBrandOrderInput = {
  readonly orderId: string;
  readonly brandId: string;
  readonly externalOrderRef?: string | null;
};

export async function recordBrandOrder(
  input: RecordBrandOrderInput,
): Promise<BrandOrder> {
  return apiFetch<BrandOrder>("/cloud-kitchen/brand-orders", {
    method: "POST",
    json: input,
  });
}

export async function listBrandOrders(
  brandId: string,
): Promise<readonly BrandOrder[]> {
  return apiFetch<readonly BrandOrder[]>(
    `/cloud-kitchen/brands/${brandId}/orders`,
  );
}
