import { apiFetch } from "./fetcher";

export type BatchState = "received" | "active" | "sold_out" | "recalled";

export type TransactionKind =
  | "received"
  | "sold"
  | "adjusted"
  | "destroyed"
  | "recalled";

export type MetrcSyncStatus = "pending" | "synced" | "failed";

export type CannabisBatch = {
  readonly id: string;
  readonly batchId: string;
  readonly productId: string;
  readonly strainName: string;
  readonly thcPct: string;
  readonly cbdPct: string;
  readonly harvestedOn: string;
  readonly expiresOn: string;
  readonly quantityGrams: string;
  readonly state: BatchState;
};

export type CannabisTransaction = {
  readonly id: string;
  readonly batchId: string;
  readonly kind: TransactionKind;
  readonly gramsDelta: string;
  readonly orderId: string | null;
  readonly customerId: string | null;
  readonly reason: string | null;
  readonly recordedByUserId: string | null;
  readonly recordedAt: string;
  readonly metrcSyncStatus: MetrcSyncStatus;
  readonly metrcSyncError: string | null;
};

export async function listBatches(
  state?: BatchState,
): Promise<readonly CannabisBatch[]> {
  const sp = new URLSearchParams();
  if (state) sp.set("state", state);
  const q = sp.toString();
  return apiFetch<readonly CannabisBatch[]>(
    `/cannabis/batches${q ? `?${q}` : ""}`,
  );
}

export async function getBatch(batchId: string): Promise<CannabisBatch> {
  return apiFetch<CannabisBatch>(`/cannabis/batches/${batchId}`);
}

export type BatchCreateInput = {
  readonly batchId: string;
  readonly productId: string;
  readonly strainName: string;
  readonly thcPct?: number | string;
  readonly cbdPct?: number | string;
  readonly harvestedOn: string;
  readonly expiresOn: string;
  readonly quantityGrams: number | string;
};

export async function receiveBatch(input: BatchCreateInput): Promise<CannabisBatch> {
  return apiFetch<CannabisBatch>("/cannabis/batches", {
    method: "POST",
    json: input,
  });
}

export type SellInput = {
  readonly batchId: string;
  readonly customerId: string;
  readonly grams: number | string;
  readonly orderId?: string | null;
};

export async function sell(input: SellInput): Promise<CannabisTransaction> {
  return apiFetch<CannabisTransaction>("/cannabis/sell", {
    method: "POST",
    json: input,
  });
}

export type DestroyInput = {
  readonly batchId: string;
  readonly grams: number | string;
  readonly reason: string;
};

export async function destroy(input: DestroyInput): Promise<CannabisTransaction> {
  return apiFetch<CannabisTransaction>("/cannabis/destroy", {
    method: "POST",
    json: input,
  });
}

export type RecallInput = {
  readonly batchId: string;
  readonly reason: string;
};

export async function recall(input: RecallInput): Promise<CannabisTransaction> {
  return apiFetch<CannabisTransaction>("/cannabis/recall", {
    method: "POST",
    json: input,
  });
}

export async function listUnsynced(): Promise<readonly CannabisTransaction[]> {
  return apiFetch<readonly CannabisTransaction[]>("/cannabis/unsynced");
}

export async function markSynced(
  transactionId: string,
): Promise<CannabisTransaction> {
  return apiFetch<CannabisTransaction>(
    `/cannabis/transactions/${transactionId}/mark-synced`,
    { method: "POST" },
  );
}

export async function markSyncFailed(
  transactionId: string,
  error: string,
): Promise<CannabisTransaction> {
  return apiFetch<CannabisTransaction>(
    `/cannabis/transactions/${transactionId}/mark-sync-failed`,
    { method: "POST", json: { error } },
  );
}
