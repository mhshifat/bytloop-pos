import { apiFetch } from "./fetcher";

export type DriveThruStatus =
  | "ordering"
  | "preparing"
  | "ready"
  | "served"
  | "abandoned";

export type DriveThruTicket = {
  readonly id: string;
  readonly orderId: string;
  readonly callNumber: number;
  readonly status: DriveThruStatus;
  readonly lane: string | null;
  readonly estimatedReadyAt: string | null;
  readonly calledAt: string | null;
  readonly servedAt: string | null;
  readonly createdAt: string;
};

export type Board = {
  readonly ordering: readonly DriveThruTicket[];
  readonly preparing: readonly DriveThruTicket[];
  readonly ready: readonly DriveThruTicket[];
};

export type CreateTicketInput = {
  readonly orderId: string;
  readonly lane?: string | null;
  readonly estimatedReadyAt?: string | null;
};

export async function createTicket(input: CreateTicketInput): Promise<DriveThruTicket> {
  return apiFetch<DriveThruTicket>("/qsr/tickets", { method: "POST", json: input });
}

export async function listActiveTickets(): Promise<readonly DriveThruTicket[]> {
  return apiFetch<readonly DriveThruTicket[]>("/qsr/tickets");
}

export async function getTicket(ticketId: string): Promise<DriveThruTicket> {
  return apiFetch<DriveThruTicket>(`/qsr/tickets/${ticketId}`);
}

export async function markPreparing(ticketId: string): Promise<DriveThruTicket> {
  return apiFetch<DriveThruTicket>(`/qsr/tickets/${ticketId}/preparing`, {
    method: "POST",
  });
}

export async function markReady(ticketId: string): Promise<DriveThruTicket> {
  return apiFetch<DriveThruTicket>(`/qsr/tickets/${ticketId}/ready`, {
    method: "POST",
  });
}

export async function callUp(ticketId: string): Promise<DriveThruTicket> {
  return apiFetch<DriveThruTicket>(`/qsr/tickets/${ticketId}/call`, {
    method: "POST",
  });
}

export async function markServed(ticketId: string): Promise<DriveThruTicket> {
  return apiFetch<DriveThruTicket>(`/qsr/tickets/${ticketId}/served`, {
    method: "POST",
  });
}

export async function abandonTicket(ticketId: string): Promise<DriveThruTicket> {
  return apiFetch<DriveThruTicket>(`/qsr/tickets/${ticketId}/abandon`, {
    method: "POST",
  });
}

export async function fetchBoard(): Promise<Board> {
  return apiFetch<Board>("/qsr/board");
}
