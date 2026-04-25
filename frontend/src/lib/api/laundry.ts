import { apiFetch } from "./fetcher";

export type LaundryStatus =
  | "received"
  | "washing"
  | "ready"
  | "collected"
  | "lost";

export type LaundryTicket = {
  readonly id: string;
  readonly customerId: string | null;
  readonly ticketNo: string;
  readonly itemCount: number;
  readonly status: LaundryStatus;
  readonly orderId: string | null;
  readonly droppedAt: string;
  readonly promisedAt: string | null;
  readonly collectedAt: string | null;
};

export type LaundryItem = {
  readonly id: string;
  readonly ticketId: string;
  readonly description: string;
  readonly quantity: number;
  readonly serviceType: string;
  readonly priceCents: number;
};

export async function listLaundryTickets(
  status?: LaundryStatus,
): Promise<readonly LaundryTicket[]> {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  return apiFetch<readonly LaundryTicket[]>(`/laundry/tickets${query}`);
}

export async function createLaundryTicket(input: {
  readonly customerId?: string | null;
  readonly ticketNo: string;
  readonly itemCount?: number;
  readonly promisedAt?: string | null;
}): Promise<LaundryTicket> {
  return apiFetch<LaundryTicket>("/laundry/tickets", {
    method: "POST",
    json: {
      customerId: input.customerId ?? null,
      ticketNo: input.ticketNo,
      itemCount: input.itemCount ?? 0,
      promisedAt: input.promisedAt ?? null,
    },
  });
}

export async function getLaundryTicket(
  ticketId: string,
): Promise<LaundryTicket> {
  return apiFetch<LaundryTicket>(`/laundry/tickets/${ticketId}`);
}

export async function listLaundryItems(
  ticketId: string,
): Promise<readonly LaundryItem[]> {
  return apiFetch<readonly LaundryItem[]>(`/laundry/tickets/${ticketId}/items`);
}

export async function addLaundryItems(
  ticketId: string,
  items: readonly {
    readonly description: string;
    readonly quantity?: number;
    readonly serviceType?: string;
    readonly priceCents: number;
  }[],
): Promise<readonly LaundryItem[]> {
  return apiFetch<readonly LaundryItem[]>(`/laundry/tickets/${ticketId}/items`, {
    method: "POST",
    json: items.map((i) => ({
      description: i.description,
      quantity: i.quantity ?? 1,
      serviceType: i.serviceType ?? "",
      priceCents: i.priceCents,
    })),
  });
}

export async function markLaundryReady(
  ticketId: string,
): Promise<LaundryTicket> {
  return apiFetch<LaundryTicket>(`/laundry/tickets/${ticketId}/ready`, {
    method: "POST",
  });
}

export async function markLaundryCollected(
  ticketId: string,
  input: { readonly orderId?: string | null } = {},
): Promise<LaundryTicket> {
  return apiFetch<LaundryTicket>(`/laundry/tickets/${ticketId}/collect`, {
    method: "POST",
    json: { orderId: input.orderId ?? null },
  });
}
