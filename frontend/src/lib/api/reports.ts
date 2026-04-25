import { apiFetch } from "./fetcher";

export type SalesSummary = {
  readonly orderCount: number;
  readonly revenueCents: number;
};

export type DashboardSnapshot = {
  readonly today: SalesSummary;
  readonly last7Days: SalesSummary;
  readonly customerCount: number;
  readonly lowStockCount: number;
};

export async function getDashboardReport(): Promise<DashboardSnapshot> {
  return apiFetch<DashboardSnapshot>("/reports/dashboard");
}

export type DailySalesPoint = {
  readonly day: string;
  readonly orderCount: number;
  readonly revenueCents: number;
};

export async function getSalesByDay(days = 14): Promise<readonly DailySalesPoint[]> {
  return apiFetch<readonly DailySalesPoint[]>(`/reports/sales-by-day?days=${days}`);
}

export type TopProductPoint = {
  readonly productId: string;
  readonly name: string;
  readonly sku: string;
  readonly unitsSold: number;
  readonly revenueCents: number;
};

export async function getTopProducts(params: {
  readonly days?: number;
  readonly limit?: number;
} = {}): Promise<readonly TopProductPoint[]> {
  const sp = new URLSearchParams();
  if (params.days) sp.set("days", String(params.days));
  if (params.limit) sp.set("limit", String(params.limit));
  const q = sp.toString();
  return apiFetch<readonly TopProductPoint[]>(
    `/reports/top-products${q ? `?${q}` : ""}`,
  );
}

export type PaymentMethodPoint = {
  readonly method: string;
  readonly orderCount: number;
  readonly amountCents: number;
};

export async function getPaymentBreakdown(
  days = 30,
): Promise<readonly PaymentMethodPoint[]> {
  return apiFetch<readonly PaymentMethodPoint[]>(
    `/reports/payment-breakdown?days=${days}`,
  );
}
