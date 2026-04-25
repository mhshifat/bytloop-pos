import { apiFetch } from "./fetcher";

export type CustomOrderStatus =
  | "quoted"
  | "in_production"
  | "ready"
  | "delivered"
  | "cancelled";

export type CustomOrder = {
  readonly id: string;
  readonly productId: string;
  readonly description: string;
  readonly quotedPriceCents: number;
  readonly customerId: string | null;
  readonly dimensionsCm: string | null;
  readonly material: string | null;
  readonly finish: string | null;
  readonly status: CustomOrderStatus;
  readonly estimatedReadyOn: string | null;
  readonly orderId: string | null;
  readonly createdAt: string;
  readonly updatedAt: string;
};

export async function listCustomOrders(
  params: {
    readonly customerId?: string;
    readonly status?: CustomOrderStatus;
  } = {},
): Promise<readonly CustomOrder[]> {
  const sp = new URLSearchParams();
  if (params.customerId) sp.set("customerId", params.customerId);
  if (params.status) sp.set("status", params.status);
  const qs = sp.toString();
  return apiFetch<readonly CustomOrder[]>(
    `/furniture/custom-orders${qs ? `?${qs}` : ""}`,
  );
}

export type QuoteInput = {
  readonly productId: string;
  readonly description: string;
  readonly quotedPriceCents: number;
  readonly customerId?: string | null;
  readonly dimensionsCm?: string | null;
  readonly material?: string | null;
  readonly finish?: string | null;
  readonly estimatedReadyOn?: string | null;
};

export async function quoteOrder(input: QuoteInput): Promise<CustomOrder> {
  return apiFetch<CustomOrder>("/furniture/custom-orders", {
    method: "POST",
    json: input,
  });
}

export async function getCustomOrder(orderId: string): Promise<CustomOrder> {
  return apiFetch<CustomOrder>(`/furniture/custom-orders/${orderId}`);
}

export type UpdateQuoteInput = {
  readonly description?: string;
  readonly quotedPriceCents?: number;
  readonly dimensionsCm?: string | null;
  readonly material?: string | null;
  readonly finish?: string | null;
  readonly estimatedReadyOn?: string | null;
};

export async function updateCustomOrder(
  orderId: string,
  input: UpdateQuoteInput,
): Promise<CustomOrder> {
  return apiFetch<CustomOrder>(`/furniture/custom-orders/${orderId}`, {
    method: "PATCH",
    json: input,
  });
}

export async function startProduction(
  orderId: string,
  input: { readonly estimatedReadyOn?: string | null } = {},
): Promise<CustomOrder> {
  return apiFetch<CustomOrder>(
    `/furniture/custom-orders/${orderId}/start-production`,
    { method: "POST", json: input },
  );
}

export async function markReady(orderId: string): Promise<CustomOrder> {
  return apiFetch<CustomOrder>(
    `/furniture/custom-orders/${orderId}/mark-ready`,
    { method: "POST", json: {} },
  );
}

export async function markDelivered(
  orderId: string,
  input: { readonly orderId?: string | null } = {},
): Promise<CustomOrder> {
  return apiFetch<CustomOrder>(
    `/furniture/custom-orders/${orderId}/mark-delivered`,
    { method: "POST", json: input },
  );
}

export async function cancelCustomOrder(
  orderId: string,
  input: { readonly reason?: string | null } = {},
): Promise<CustomOrder> {
  return apiFetch<CustomOrder>(
    `/furniture/custom-orders/${orderId}/cancel`,
    { method: "POST", json: input },
  );
}
