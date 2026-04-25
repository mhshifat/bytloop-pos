import { apiFetch } from "./fetcher";

export type OrderType = "retail" | "dine_in" | "takeaway" | "delivery" | "appointment" | "job_card" | "rental";
export type PaymentMethod = "cash" | "card" | "bkash" | "nagad" | "sslcommerz" | "rocket" | "stripe" | "paypal";

export type CheckoutCartItem = {
  readonly productId: string;
  readonly quantity: number;
  readonly verticalData?: Record<string, unknown>;
  readonly exciseCents?: number;
};

export type AgeVerificationCheckout = {
  readonly customerDob: string;
  readonly productIds?: readonly string[];
};

export type CheckoutRequest = {
  readonly items: readonly CheckoutCartItem[];
  readonly orderType?: OrderType;
  readonly paymentMethod?: PaymentMethod;
  readonly amountTenderedCents?: number;
  readonly customerId?: string | null;
  readonly discountCode?: string | null;
  readonly orderVerticalData?: Record<string, unknown>;
  readonly ageVerification?: AgeVerificationCheckout;
};

export type OrderRead = {
  readonly id: string;
  readonly number: string;
  readonly orderType: OrderType;
  readonly status: "open" | "completed" | "voided" | "refunded";
  readonly currency: string;
  readonly subtotalCents: number;
  readonly taxCents: number;
  readonly discountCents: number;
  readonly totalCents: number;
  readonly customerId?: string | null;
  readonly items: readonly {
    readonly id: string;
    readonly productId: string;
    readonly nameSnapshot: string;
    readonly unitPriceCents: number;
    readonly quantity: number;
    readonly lineTotalCents: number;
    readonly verticalData?: Record<string, unknown>;
  }[];
  readonly payments: readonly {
    readonly id: string;
    readonly method: PaymentMethod;
    readonly amountCents: number;
    readonly currency: string;
  }[];
  readonly changeDueCents: number;
};

export async function checkout(req: CheckoutRequest): Promise<OrderRead> {
  return apiFetch<OrderRead>("/orders/checkout", { method: "POST", json: req });
}

export type OrderSummary = {
  readonly id: string;
  readonly number: string;
  readonly status: "open" | "completed" | "voided" | "refunded";
  readonly orderType: OrderType;
  readonly currency: string;
  readonly totalCents: number;
  readonly customerId?: string | null;
  readonly openedAt: string;
  readonly closedAt: string | null;
};

export type OrderList = {
  readonly items: readonly OrderSummary[];
  readonly hasMore: boolean;
  readonly page: number;
  readonly pageSize: number;
};

export async function listOrders(params: {
  readonly page?: number;
  readonly pageSize?: number;
  readonly status?: OrderSummary["status"];
  readonly since?: string;
  readonly until?: string;
} = {}): Promise<OrderList> {
  const sp = new URLSearchParams();
  if (params.page) sp.set("page", String(params.page));
  if (params.pageSize) sp.set("pageSize", String(params.pageSize));
  if (params.status) sp.set("status", params.status);
  if (params.since) sp.set("since", params.since);
  if (params.until) sp.set("until", params.until);
  const q = sp.toString();
  return apiFetch<OrderList>(`/orders${q ? `?${q}` : ""}`);
}

export async function getOrder(orderId: string): Promise<OrderRead> {
  return apiFetch<OrderRead>(`/orders/${orderId}`);
}

export async function voidOrder(orderId: string): Promise<OrderRead> {
  return apiFetch<OrderRead>(`/orders/${orderId}/void`, { method: "POST" });
}

export async function refundOrder(orderId: string): Promise<OrderRead> {
  return apiFetch<OrderRead>(`/orders/${orderId}/refund`, { method: "POST" });
}
