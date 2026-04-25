import { apiFetch } from "./fetcher";

export type KdsStation = "kitchen" | "bar" | "dessert" | "expo";
export type KotStatus = "new" | "preparing" | "ready" | "served" | "cancelled";

export type KotTicket = {
  readonly id: string;
  readonly orderId: string;
  readonly number: string;
  readonly station: KdsStation;
  readonly status: KotStatus;
  readonly course: number;
  readonly firedAt: string;
  readonly readyAt: string | null;
};

export async function kdsQueue(station: KdsStation = "kitchen"): Promise<KotTicket[]> {
  return apiFetch<KotTicket[]>(`/restaurant/kds?station=${station}`);
}

export async function updateKotStatus(
  ticketId: string,
  status: KotStatus,
): Promise<KotTicket> {
  return apiFetch<KotTicket>(`/restaurant/kot/${ticketId}/status`, {
    method: "PATCH",
    json: { status },
  });
}

export type StationRoute = {
  readonly id: string;
  readonly productId: string;
  readonly station: KdsStation;
  readonly course: number;
};

export async function listStationRoutes(): Promise<readonly StationRoute[]> {
  return apiFetch<readonly StationRoute[]>("/restaurant/routes");
}

export async function upsertStationRoute(input: {
  readonly productId: string;
  readonly station: KdsStation;
  readonly course: number;
}): Promise<StationRoute> {
  return apiFetch<StationRoute>("/restaurant/routes", { method: "PUT", json: input });
}

export type FireOrderRequest = {
  readonly orderId: string;
  readonly items: readonly {
    readonly productId: string;
    readonly nameSnapshot: string;
    readonly quantity: number;
    readonly modifierNotes?: string | null;
  }[];
};

export async function fireOrder(input: FireOrderRequest): Promise<readonly KotTicket[]> {
  return apiFetch<readonly KotTicket[]>("/restaurant/kot/fire-order", {
    method: "POST",
    json: input,
  });
}
