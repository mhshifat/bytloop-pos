import { apiFetch } from "./fetcher";

export type EventStatus = "active" | "cancelled";
export type TicketStatus = "issued" | "scanned" | "voided";

export type EventInstance = {
  readonly id: string;
  readonly title: string;
  readonly startsAt: string;
  readonly endsAt: string;
  readonly venue: string;
  readonly status: EventStatus;
};

export type TicketType = {
  readonly id: string;
  readonly eventId: string;
  readonly code: string;
  readonly name: string;
  readonly priceCents: number;
  readonly quota: number;
  readonly soldCount: number;
};

export type IssuedTicket = {
  readonly id: string;
  readonly ticketTypeId: string;
  readonly orderId: string | null;
  readonly holderName: string;
  readonly serialNo: string;
  readonly status: TicketStatus;
  readonly scannedAt: string | null;
  readonly issuedAt: string;
};

export async function listEvents(): Promise<readonly EventInstance[]> {
  return apiFetch<readonly EventInstance[]>("/tickets/events");
}

export async function createEvent(input: {
  readonly title: string;
  readonly startsAt: string;
  readonly endsAt: string;
  readonly venue?: string;
}): Promise<EventInstance> {
  return apiFetch<EventInstance>("/tickets/events", {
    method: "POST",
    json: { ...input, venue: input.venue ?? "" },
  });
}

export async function cancelEvent(eventId: string): Promise<EventInstance> {
  return apiFetch<EventInstance>(`/tickets/events/${eventId}/cancel`, {
    method: "POST",
  });
}

export async function listTicketTypes(
  eventId: string,
): Promise<readonly TicketType[]> {
  return apiFetch<readonly TicketType[]>(`/tickets/events/${eventId}/types`);
}

export async function addTicketType(
  eventId: string,
  input: {
    readonly code: string;
    readonly name: string;
    readonly priceCents: number;
    readonly quota: number;
  },
): Promise<TicketType> {
  return apiFetch<TicketType>(`/tickets/events/${eventId}/types`, {
    method: "POST",
    json: input,
  });
}

export async function purchaseTickets(input: {
  readonly ticketTypeId: string;
  readonly quantity: number;
  readonly orderId?: string | null;
  readonly holderNames?: readonly string[];
}): Promise<readonly IssuedTicket[]> {
  return apiFetch<readonly IssuedTicket[]>("/tickets/purchase", {
    method: "POST",
    json: {
      ticketTypeId: input.ticketTypeId,
      quantity: input.quantity,
      orderId: input.orderId ?? null,
      holderNames: input.holderNames ?? [],
    },
  });
}

export async function scanTicket(serialNo: string): Promise<IssuedTicket> {
  return apiFetch<IssuedTicket>("/tickets/scan", {
    method: "POST",
    json: { serialNo },
  });
}

export async function voidTicket(serialNo: string): Promise<IssuedTicket> {
  return apiFetch<IssuedTicket>("/tickets/void", {
    method: "POST",
    json: { serialNo },
  });
}

export async function listIssuedTickets(
  ticketTypeId: string,
): Promise<readonly IssuedTicket[]> {
  return apiFetch<readonly IssuedTicket[]>(
    `/tickets/types/${ticketTypeId}/issued`,
  );
}
