import { apiFetch } from "./fetcher";

export async function suggestStaffSchedule(): Promise<{
  readonly shifts: readonly { readonly day: string; readonly startHour: number; readonly endHour: number; readonly staffId: string | null; readonly roleHint: string }[];
  readonly staffPerHour: Record<string, number>;
}> {
  return apiFetch("/ai/ops/staff-schedule/suggest");
}

export async function optimizeRoute(day: string): Promise<{ readonly day: string; readonly stops: readonly any[] }> {
  const sp = new URLSearchParams();
  sp.set("day", day);
  return apiFetch(`/ai/ops/deliveries/route-optimize?${sp.toString()}`);
}

export async function predictQsrPrepTime(ticketId: string): Promise<{ readonly ok: boolean; readonly estimatedReadyAt?: string; readonly baseMinutes?: number; readonly error?: string }> {
  return apiFetch("/ai/ops/qsr/prep-time/predict", { method: "POST", json: { ticketId } });
}

export async function tableTurnForecast(): Promise<{ readonly items: readonly any[]; readonly assumedMinutes: number }> {
  return apiFetch("/ai/ops/restaurant/table-turn");
}

export async function stylistMatch(customerId: string): Promise<{ readonly suggestedStaffId: string | null; readonly reason: string }> {
  const sp = new URLSearchParams();
  sp.set("customerId", customerId);
  return apiFetch(`/ai/ops/salon/stylist-match?${sp.toString()}`);
}

