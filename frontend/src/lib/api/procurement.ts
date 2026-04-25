import { apiFetch } from "./fetcher";

export type Supplier = {
  readonly id: string;
  readonly name: string;
  readonly email: string | null;
  readonly phone: string | null;
  readonly address: string | null;
};

export type PurchaseOrderStatus =
  | "draft"
  | "sent"
  | "partially_received"
  | "received"
  | "closed"
  | "cancelled";

export type PurchaseOrderItem = {
  readonly id: string;
  readonly productId: string;
  readonly quantityOrdered: number;
  readonly quantityReceived: number;
  readonly unitCostCents: number;
  readonly lineTotalCents: number;
};

export type PurchaseOrderSummary = {
  readonly id: string;
  readonly supplierId: string;
  readonly number: string;
  readonly status: PurchaseOrderStatus;
  readonly totalCents: number;
  readonly currency: string;
  readonly createdAt: string;
};

export type PurchaseOrder = PurchaseOrderSummary & {
  readonly sentAt: string | null;
  readonly closedAt: string | null;
  readonly items: readonly PurchaseOrderItem[];
};

export type PurchaseOrderList = {
  readonly items: readonly PurchaseOrderSummary[];
  readonly hasMore: boolean;
  readonly page: number;
  readonly pageSize: number;
};

export async function listSuppliers(): Promise<readonly Supplier[]> {
  return apiFetch<readonly Supplier[]>("/suppliers");
}

export type SupplierCreateInput = {
  readonly name: string;
  readonly email?: string | null;
  readonly phone?: string | null;
  readonly address?: string | null;
};

export async function createSupplier(input: SupplierCreateInput): Promise<Supplier> {
  return apiFetch<Supplier>("/suppliers", { method: "POST", json: input });
}

export async function listPurchaseOrders(
  params: { readonly page?: number; readonly pageSize?: number } = {},
): Promise<PurchaseOrderList> {
  const sp = new URLSearchParams();
  if (params.page) sp.set("page", String(params.page));
  if (params.pageSize) sp.set("pageSize", String(params.pageSize));
  const q = sp.toString();
  return apiFetch<PurchaseOrderList>(`/purchase-orders${q ? `?${q}` : ""}`);
}

export type PurchaseOrderCreateInput = {
  readonly supplierId: string;
  readonly currency: string;
  readonly items: readonly {
    readonly productId: string;
    readonly quantityOrdered: number;
    readonly unitCostCents: number;
  }[];
};

export async function createPurchaseOrder(
  input: PurchaseOrderCreateInput,
): Promise<PurchaseOrder> {
  return apiFetch<PurchaseOrder>("/purchase-orders", {
    method: "POST",
    json: input,
  });
}

export async function getPurchaseOrder(id: string): Promise<PurchaseOrder> {
  return apiFetch<PurchaseOrder>(`/purchase-orders/${id}`);
}

export type ReceiveInput = {
  readonly items: readonly { readonly purchaseOrderItemId: string; readonly quantity: number }[];
};

export async function receivePurchaseOrder(
  purchaseOrderId: string,
  input: ReceiveInput,
): Promise<PurchaseOrder> {
  return apiFetch<PurchaseOrder>(
    `/purchase-orders/${purchaseOrderId}/receive`,
    { method: "POST", json: input },
  );
}
