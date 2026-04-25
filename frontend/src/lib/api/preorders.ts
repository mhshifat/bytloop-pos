import { apiFetch } from "./fetcher";

export type PreorderStatus =
  | "pending"
  | "preparing"
  | "ready"
  | "picked_up"
  | "cancelled";

export type PreorderItem = {
  readonly id: string;
  readonly productId: string;
  readonly quantity: number;
  readonly unitPriceCents: number;
};

export type Preorder = {
  readonly id: string;
  readonly customerId: string | null;
  readonly pickupAt: string;
  readonly status: PreorderStatus;
  readonly orderId: string | null;
  readonly notes: string | null;
  readonly totalCents: number;
  readonly items: readonly PreorderItem[];
};

export type PreorderCreateInput = {
  readonly customerId?: string | null;
  readonly pickupAt: string;
  readonly notes?: string | null;
  readonly items: readonly {
    readonly productId: string;
    readonly quantity: number;
    readonly unitPriceCents: number;
  }[];
};

export async function createPreorder(
  input: PreorderCreateInput,
): Promise<Preorder> {
  return apiFetch<Preorder>("/preorders", { method: "POST", json: input });
}

export async function listUpcomingPreorders(
  days = 7,
): Promise<readonly Preorder[]> {
  return apiFetch<readonly Preorder[]>(`/preorders?days=${days}`);
}

export async function listPreordersForDay(
  day: string,
): Promise<readonly Preorder[]> {
  return apiFetch<readonly Preorder[]>(`/preorders/by-day?day=${day}`);
}

export async function getPreorder(preorderId: string): Promise<Preorder> {
  return apiFetch<Preorder>(`/preorders/${preorderId}`);
}

export async function updatePreorderStatus(
  preorderId: string,
  status: PreorderStatus,
): Promise<Preorder> {
  return apiFetch<Preorder>(`/preorders/${preorderId}/status`, {
    method: "PATCH",
    json: { status },
  });
}

export type PaymentMethod =
  | "cash"
  | "card"
  | "bkash"
  | "nagad"
  | "sslcommerz"
  | "rocket"
  | "stripe"
  | "paypal";

export async function convertPreorderToOrder(
  preorderId: string,
  input: {
    readonly paymentMethod?: PaymentMethod;
    readonly amountTenderedCents?: number | null;
    readonly paymentReference?: string | null;
  } = {},
): Promise<Preorder> {
  return apiFetch<Preorder>(`/preorders/${preorderId}/convert`, {
    method: "POST",
    json: {
      paymentMethod: input.paymentMethod ?? "cash",
      amountTenderedCents: input.amountTenderedCents ?? null,
      paymentReference: input.paymentReference ?? null,
    },
  });
}
