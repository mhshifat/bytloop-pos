import { apiFetch } from "./fetcher";

export type TapOutcome = "approved" | "declined" | "cancelled" | "error";

export type SoftposReader = {
  readonly id: string;
  readonly deviceLabel: string;
  readonly deviceFingerprint: string;
  readonly isCertified: boolean;
  readonly certifiedAt: string | null;
  readonly lastSeenAt: string | null;
};

export type SoftposTapEvent = {
  readonly id: string;
  readonly readerId: string;
  readonly amountCents: number;
  readonly cardBin: string;
  readonly outcome: TapOutcome;
  readonly providerReference: string | null;
  readonly tappedAt: string;
};

export type ReaderActivity = {
  readonly readerId: string;
  readonly since: string | null;
  readonly until: string | null;
  readonly approvedCount: number;
  readonly declinedCount: number;
  readonly cancelledCount: number;
  readonly errorCount: number;
  readonly approvedAmountCents: number;
  readonly events: readonly SoftposTapEvent[];
};

export async function listReaders(): Promise<readonly SoftposReader[]> {
  return apiFetch<readonly SoftposReader[]>("/softpos/readers");
}

export async function registerReader(input: {
  readonly deviceLabel: string;
  readonly deviceFingerprint: string;
}): Promise<SoftposReader> {
  return apiFetch<SoftposReader>("/softpos/readers", {
    method: "POST",
    json: input,
  });
}

export async function certifyReader(readerId: string): Promise<SoftposReader> {
  return apiFetch<SoftposReader>(`/softpos/readers/${readerId}/certify`, {
    method: "POST",
  });
}

export async function recordTap(
  readerId: string,
  input: {
    readonly amountCents: number;
    readonly cardBin: string;
    readonly outcome: TapOutcome;
    readonly providerReference?: string | null;
  },
): Promise<SoftposTapEvent> {
  return apiFetch<SoftposTapEvent>(`/softpos/readers/${readerId}/taps`, {
    method: "POST",
    json: input,
  });
}

export async function readerActivity(
  readerId: string,
  range: { readonly since?: string; readonly until?: string } = {},
): Promise<ReaderActivity> {
  const sp = new URLSearchParams();
  if (range.since) sp.set("since", range.since);
  if (range.until) sp.set("until", range.until);
  const qs = sp.toString();
  return apiFetch<ReaderActivity>(
    `/softpos/readers/${readerId}/activity${qs ? `?${qs}` : ""}`,
  );
}
