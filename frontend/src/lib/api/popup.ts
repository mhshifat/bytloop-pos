import { apiFetch } from "./fetcher";

export type PopupEvent = {
  readonly id: string;
  readonly code: string;
  readonly name: string;
  readonly venue: string;
  readonly startsAt: string;
  readonly endsAt: string;
  readonly locationNotes: string | null;
};

export type PopupStall = {
  readonly id: string;
  readonly eventId: string;
  readonly stallLabel: string;
  readonly operatorUserId: string | null;
};

export type PopupInventorySnapshot = {
  readonly id: string;
  readonly eventId: string;
  readonly productId: string;
  readonly openingStock: number;
  readonly closingStock: number | null;
  readonly openedAt: string;
  readonly closedAt: string | null;
};

export type PopupSoldLine = {
  readonly productId: string;
  readonly openingStock: number;
  readonly closingStock: number;
  readonly soldCount: number;
};

export type PopupCloseReport = {
  readonly eventId: string;
  readonly lines: readonly PopupSoldLine[];
  readonly totalSoldUnits: number;
};

export async function listEvents(): Promise<readonly PopupEvent[]> {
  return apiFetch<readonly PopupEvent[]>("/popup/events");
}

export async function createEvent(input: {
  readonly code: string;
  readonly name: string;
  readonly venue: string;
  readonly startsAt: string;
  readonly endsAt: string;
  readonly locationNotes?: string | null;
}): Promise<PopupEvent> {
  return apiFetch<PopupEvent>("/popup/events", { method: "POST", json: input });
}

export async function createStall(input: {
  readonly eventId: string;
  readonly stallLabel: string;
  readonly operatorUserId?: string | null;
}): Promise<PopupStall> {
  return apiFetch<PopupStall>("/popup/stalls", { method: "POST", json: input });
}

export async function listStalls(eventId: string): Promise<readonly PopupStall[]> {
  return apiFetch<readonly PopupStall[]>(`/popup/events/${eventId}/stalls`);
}

export async function openEvent(
  eventId: string,
): Promise<readonly PopupInventorySnapshot[]> {
  return apiFetch<readonly PopupInventorySnapshot[]>(
    `/popup/events/${eventId}/open`,
    { method: "POST" },
  );
}

export async function closeEvent(eventId: string): Promise<PopupCloseReport> {
  return apiFetch<PopupCloseReport>(`/popup/events/${eventId}/close`, {
    method: "POST",
  });
}
