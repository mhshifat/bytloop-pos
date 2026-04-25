import { apiFetch } from "./fetcher";

export type SelfCheckoutStatus =
  | "scanning"
  | "awaiting_approval"
  | "completed"
  | "abandoned";

export type SelfCheckoutSession = {
  readonly id: string;
  readonly stationLabel: string;
  readonly customerIdentifier: string | null;
  readonly status: SelfCheckoutStatus;
  readonly startedAt: string;
  readonly completedAt: string | null;
  readonly orderId: string | null;
};

export type SelfCheckoutScan = {
  readonly id: string;
  readonly sessionId: string;
  readonly barcode: string;
  readonly productId: string | null;
  readonly quantity: number;
  readonly unitPriceCents: number;
  readonly scannedAt: string;
  readonly flaggedForStaff: boolean;
  readonly flagReason: string | null;
};

export async function startSession(input: {
  readonly stationLabel: string;
  readonly customerIdentifier?: string | null;
}): Promise<SelfCheckoutSession> {
  return apiFetch<SelfCheckoutSession>("/self-checkout/sessions", {
    method: "POST",
    json: input,
  });
}

export async function scan(
  sessionId: string,
  input: { readonly barcode: string; readonly quantity?: number },
): Promise<SelfCheckoutScan> {
  return apiFetch<SelfCheckoutScan>(
    `/self-checkout/sessions/${sessionId}/scans`,
    { method: "POST", json: input },
  );
}

export async function completeSession(
  sessionId: string,
  input: { readonly staffUserId?: string | null } = {},
): Promise<SelfCheckoutSession> {
  return apiFetch<SelfCheckoutSession>(
    `/self-checkout/sessions/${sessionId}/complete`,
    { method: "POST", json: input },
  );
}

export async function abandonSession(
  sessionId: string,
): Promise<SelfCheckoutSession> {
  return apiFetch<SelfCheckoutSession>(
    `/self-checkout/sessions/${sessionId}/abandon`,
    { method: "POST" },
  );
}

export async function getSession(
  sessionId: string,
): Promise<SelfCheckoutSession> {
  return apiFetch<SelfCheckoutSession>(`/self-checkout/sessions/${sessionId}`);
}

export async function listScans(
  sessionId: string,
): Promise<readonly SelfCheckoutScan[]> {
  return apiFetch<readonly SelfCheckoutScan[]>(
    `/self-checkout/sessions/${sessionId}/scans`,
  );
}
