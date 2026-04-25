import { apiFetch } from "./fetcher";

export type SeatStatus = "available" | "held" | "sold";

export type Show = {
  readonly id: string;
  readonly title: string;
  readonly screen: string;
  readonly startsAt: string;
  readonly endsAt: string;
  readonly ticketPriceCents: number;
};

export type Seat = {
  readonly id: string;
  readonly showId: string;
  readonly label: string;
  readonly status: SeatStatus;
  readonly heldUntil: string | null;
};

export async function listShows(): Promise<readonly Show[]> {
  return apiFetch<readonly Show[]>("/cinema/shows");
}

export async function listSeats(showId: string): Promise<readonly Seat[]> {
  return apiFetch<readonly Seat[]>(`/cinema/shows/${showId}/seats`);
}

export async function holdSeat(
  seatId: string,
  input: { readonly heldBy: string; readonly ttlSeconds?: number },
): Promise<Seat> {
  return apiFetch<Seat>(`/cinema/seats/${seatId}/hold`, {
    method: "POST",
    json: { heldBy: input.heldBy, ttlSeconds: input.ttlSeconds ?? 600 },
  });
}

export async function releaseSeat(
  seatId: string,
  heldBy: string,
): Promise<Seat> {
  return apiFetch<Seat>(`/cinema/seats/${seatId}/release`, {
    method: "POST",
    json: { heldBy },
  });
}

export async function sellSeat(
  seatId: string,
  input: { readonly orderId?: string | null; readonly heldBy?: string | null } = {},
): Promise<Seat> {
  return apiFetch<Seat>(`/cinema/seats/${seatId}/sell`, {
    method: "POST",
    json: { orderId: input.orderId ?? null, heldBy: input.heldBy ?? null },
  });
}

export type ShowCreateInput = {
  readonly title: string;
  readonly screen: string;
  readonly startsAt: string;
  readonly endsAt: string;
  readonly ticketPriceCents: number;
  readonly seatLabels?: readonly string[];
  readonly seatMapRows?: number;
  readonly seatMapCols?: number;
};

export async function createShow(input: ShowCreateInput): Promise<Show> {
  return apiFetch<Show>("/cinema/shows", { method: "POST", json: input });
}
