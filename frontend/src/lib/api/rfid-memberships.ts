import { apiFetch } from "./fetcher";

export type PassStatus = "active" | "suspended" | "expired";

export type RfidPass = {
  readonly id: string;
  readonly rfidTag: string;
  readonly customerId: string | null;
  readonly planCode: string;
  readonly balanceUses: number | null;
  readonly expiresOn: string | null;
  readonly status: PassStatus;
  readonly createdAt: string;
};

export type PassUse = {
  readonly id: string;
  readonly passId: string;
  readonly location: string;
  readonly usedAt: string;
};

export type RedeemResult = {
  readonly success: boolean;
  readonly reason: string | null;
  readonly passId: string | null;
  readonly balanceUsesRemaining: number | null;
};

export async function listPasses(): Promise<readonly RfidPass[]> {
  return apiFetch<readonly RfidPass[]>("/rfid/passes");
}

export async function issuePass(input: {
  readonly rfidTag: string;
  readonly customerId?: string | null;
  readonly planCode: string;
  readonly balanceUses?: number | null;
  readonly expiresOn?: string | null;
}): Promise<RfidPass> {
  return apiFetch<RfidPass>("/rfid/passes", {
    method: "POST",
    json: {
      rfidTag: input.rfidTag,
      customerId: input.customerId ?? null,
      planCode: input.planCode,
      balanceUses: input.balanceUses ?? null,
      expiresOn: input.expiresOn ?? null,
    },
  });
}

export async function updatePassStatus(
  passId: string,
  status: PassStatus,
): Promise<RfidPass> {
  return apiFetch<RfidPass>(`/rfid/passes/${passId}/status`, {
    method: "PATCH",
    json: { status },
  });
}

export async function redeemPass(input: {
  readonly rfidTag: string;
  readonly location?: string;
}): Promise<RedeemResult> {
  return apiFetch<RedeemResult>("/rfid/redeem", {
    method: "POST",
    json: { rfidTag: input.rfidTag, location: input.location ?? "" },
  });
}

export async function listPassTransactions(
  passId: string,
): Promise<readonly PassUse[]> {
  return apiFetch<readonly PassUse[]>(`/rfid/passes/${passId}/transactions`);
}
