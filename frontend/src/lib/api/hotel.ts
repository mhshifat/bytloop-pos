import { apiFetch } from "./fetcher";

export type ReservationStatus = "booked" | "checked_in" | "checked_out" | "cancelled";

export type Room = {
  readonly id: string;
  readonly number: string;
  readonly category: string;
  readonly nightlyRateCents: number;
};

export type Reservation = {
  readonly id: string;
  readonly roomId: string;
  readonly customerId: string;
  readonly status: ReservationStatus;
  readonly checkIn: string;
  readonly checkOut: string;
  readonly checkedInAt: string | null;
  readonly checkedOutAt: string | null;
};

export async function listRooms(): Promise<readonly Room[]> {
  return apiFetch<readonly Room[]>("/hotel/rooms");
}

export async function listReservations(): Promise<readonly Reservation[]> {
  return apiFetch<readonly Reservation[]>("/hotel/reservations");
}

export async function addRoom(input: {
  readonly number: string;
  readonly category: string;
  readonly nightlyRateCents: number;
}): Promise<Room> {
  return apiFetch<Room>("/hotel/rooms", { method: "POST", json: input });
}

export async function reserve(input: {
  readonly roomId: string;
  readonly customerId: string;
  readonly checkIn: string;
  readonly checkOut: string;
}): Promise<Reservation> {
  return apiFetch<Reservation>("/hotel/reservations", { method: "POST", json: input });
}

export async function updateReservationStatus(
  id: string,
  status: ReservationStatus,
): Promise<Reservation> {
  return apiFetch<Reservation>(`/hotel/reservations/${id}/status`, {
    method: "PATCH",
    json: { status },
  });
}

export async function availableRooms(
  checkIn: string,
  checkOut: string,
): Promise<readonly Room[]> {
  const sp = new URLSearchParams({ checkIn, checkOut });
  return apiFetch<readonly Room[]>(`/hotel/rooms/available?${sp.toString()}`);
}

export async function hotelCheckIn(reservationId: string): Promise<Reservation> {
  return apiFetch<Reservation>(`/hotel/reservations/${reservationId}/check-in`, {
    method: "POST",
  });
}

export async function hotelCheckOut(reservationId: string): Promise<Reservation> {
  return apiFetch<Reservation>(`/hotel/reservations/${reservationId}/check-out`, {
    method: "POST",
  });
}

export type FolioCharge = {
  readonly id: string;
  readonly reservationId: string;
  readonly description: string;
  readonly amountCents: number;
  readonly postedAt: string;
};

export async function postFolioCharge(
  reservationId: string,
  input: { readonly description: string; readonly amountCents: number },
): Promise<FolioCharge> {
  return apiFetch<FolioCharge>(
    `/hotel/reservations/${reservationId}/charges`,
    { method: "POST", json: input },
  );
}

export type Folio = {
  readonly reservationId: string;
  readonly nights: number;
  readonly roomTotalCents: number;
  readonly incidentalsCents: number;
  readonly totalCents: number;
  readonly charges: readonly FolioCharge[];
};

export async function getFolio(reservationId: string): Promise<Folio> {
  return apiFetch<Folio>(`/hotel/reservations/${reservationId}/folio`);
}
