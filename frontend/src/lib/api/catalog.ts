import { apiFetch } from "./fetcher";

export type Product = {
  readonly id: string;
  readonly sku: string;
  readonly barcode: string | null;
  readonly name: string;
  readonly description: string | null;
  readonly categoryId: string | null;
  readonly priceCents: number;
  readonly currency: string;
  readonly isActive: boolean;
  readonly trackInventory: boolean;
  readonly taxRate: string;
};

export type ProductList = {
  readonly items: readonly Product[];
  readonly hasMore: boolean;
  readonly page: number;
  readonly pageSize: number;
};

export type ProductQuery = {
  readonly search?: string;
  readonly categoryId?: string;
  readonly page?: number;
  readonly pageSize?: number;
};

export async function listProducts(query: ProductQuery = {}): Promise<ProductList> {
  const params = new URLSearchParams();
  if (query.search) params.set("search", query.search);
  if (query.categoryId) params.set("categoryId", query.categoryId);
  if (query.page) params.set("page", String(query.page));
  if (query.pageSize) params.set("pageSize", String(query.pageSize));
  const q = params.toString();
  return apiFetch<ProductList>(`/products${q ? `?${q}` : ""}`);
}

/** Server caps `pageSize` at 100. Use this to load many pages for UIs that need a full list (KDS routes, etc.). */
export async function listProductsAllPages(
  options: { readonly search?: string; readonly categoryId?: string; readonly maxPages?: number } = {},
): Promise<ProductList> {
  const { maxPages = 50, ...query } = options;
  const pageSize = 100;
  const items: Product[] = [];
  for (let page = 1; page <= maxPages; page += 1) {
    const batch = await listProducts({ ...query, page, pageSize });
    items.push(...batch.items);
    if (!batch.hasMore) {
      return { items, hasMore: false, page: 1, pageSize: items.length };
    }
  }
  return { items, hasMore: true, page: 1, pageSize: items.length };
}

export type ProductCreateInput = {
  readonly sku: string;
  readonly barcode?: string | null;
  readonly name: string;
  readonly description?: string | null;
  readonly categoryId?: string | null;
  readonly priceCents: number;
  readonly currency: string;
  readonly isActive?: boolean;
  readonly trackInventory?: boolean;
};

export async function createProduct(input: ProductCreateInput): Promise<Product> {
  return apiFetch<Product>("/products", { method: "POST", json: input });
}

export async function getProduct(productId: string): Promise<Product> {
  return apiFetch<Product>(`/products/${productId}`);
}

export type ProductUpdateInput = Partial<Omit<ProductCreateInput, "sku">>;

export async function updateProduct(
  productId: string,
  input: ProductUpdateInput,
): Promise<Product> {
  return apiFetch<Product>(`/products/${productId}`, {
    method: "PATCH",
    json: input,
  });
}

export async function deleteProduct(productId: string): Promise<void> {
  return apiFetch<void>(`/products/${productId}`, { method: "DELETE" });
}

export type InventoryLevel = {
  readonly id: string;
  readonly productId: string;
  readonly productName: string;
  readonly sku: string;
  readonly locationId: string;
  readonly locationCode: string;
  readonly locationName: string;
  readonly quantity: number;
  readonly reorderPoint: number;
  readonly updatedAt: string;
};

export type InventoryLevelList = {
  readonly items: readonly InventoryLevel[];
  readonly hasMore: boolean;
  readonly page: number;
  readonly pageSize: number;
};

export async function listInventoryLevels(
  params: { readonly page?: number; readonly pageSize?: number } = {},
): Promise<InventoryLevelList> {
  const sp = new URLSearchParams();
  if (params.page) sp.set("page", String(params.page));
  if (params.pageSize) sp.set("pageSize", String(params.pageSize));
  const q = sp.toString();
  return apiFetch<InventoryLevelList>(`/inventory/levels${q ? `?${q}` : ""}`);
}

export async function adjustStock(input: {
  readonly productId: string;
  readonly delta: number;
  readonly reason?: string;
}): Promise<{ readonly quantity: number }> {
  return apiFetch<{ readonly quantity: number }>("/inventory/adjust", {
    method: "POST",
    json: { productId: input.productId, delta: input.delta, reason: input.reason ?? "adjustment" },
  });
}

export async function setReorderPoint(input: {
  readonly productId: string;
  readonly reorderPoint: number;
}): Promise<{ readonly reorderPoint: number }> {
  return apiFetch<{ readonly reorderPoint: number }>("/inventory/reorder-point", {
    method: "POST",
    json: input,
  });
}

export async function transferStock(input: {
  readonly productId: string;
  readonly sourceLocationId: string;
  readonly destinationLocationId: string;
  readonly quantity: number;
}): Promise<{ readonly sourceQuantity: number; readonly destinationQuantity: number }> {
  return apiFetch<{ readonly sourceQuantity: number; readonly destinationQuantity: number }>(
    "/inventory/transfer",
    { method: "POST", json: input },
  );
}
