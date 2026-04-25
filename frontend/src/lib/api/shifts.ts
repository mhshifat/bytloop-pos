import { apiFetch } from "./fetcher";

export type Shift = {
  readonly id: string;
  readonly status: "open" | "closed";
  readonly openingFloatCents: number;
  readonly closingCountedCents: number | null;
  readonly expectedCashCents: number | null;
  readonly varianceCents: number | null;
  readonly openedAt: string;
  readonly closedAt: string | null;
};

export async function currentShift(): Promise<Shift | null> {
  return apiFetch<Shift | null>("/shifts/current");
}

export async function openShift(openingFloatCents: number): Promise<Shift> {
  return apiFetch<Shift>("/shifts/open", {
    method: "POST",
    json: { openingFloatCents },
  });
}

export async function closeShift(closingCountedCents: number): Promise<Shift> {
  return apiFetch<Shift>("/shifts/close", {
    method: "POST",
    json: { closingCountedCents },
  });
}
