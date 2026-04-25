import { apiFetch } from "./fetcher";

export type RentalStatus = "reserved" | "out" | "returned" | "overdue";

export type Asset = {
  readonly id: string;
  readonly code: string;
  readonly label: string;
  readonly hourlyRateCents: number;
  readonly dailyRateCents: number;
};

export type Contract = {
  readonly id: string;
  readonly assetId: string;
  readonly customerId: string;
  readonly status: RentalStatus;
  readonly startsAt: string;
  readonly endsAt: string;
  readonly returnedAt: string | null;
  readonly depositCents: number;
  readonly lateFeeCents: number;
  readonly damageFeeCents: number;
  readonly damageNotes: string | null;
};

export async function listAssets(): Promise<readonly Asset[]> {
  return apiFetch<readonly Asset[]>("/rental/assets");
}

export async function availableAssets(
  startsAt: string,
  endsAt: string,
): Promise<readonly Asset[]> {
  const sp = new URLSearchParams({ startsAt, endsAt });
  return apiFetch<readonly Asset[]>(`/rental/assets/available?${sp.toString()}`);
}

export async function listContracts(): Promise<readonly Contract[]> {
  return apiFetch<readonly Contract[]>("/rental/contracts");
}

export async function addAsset(input: {
  readonly code: string;
  readonly label: string;
  readonly hourlyRateCents: number;
  readonly dailyRateCents: number;
}): Promise<Asset> {
  return apiFetch<Asset>("/rental/assets", { method: "POST", json: input });
}

export async function reserveAsset(input: {
  readonly assetId: string;
  readonly customerId: string;
  readonly startsAt: string;
  readonly endsAt: string;
  readonly depositCents?: number;
}): Promise<Contract> {
  return apiFetch<Contract>("/rental/contracts", { method: "POST", json: input });
}

export async function rentalCheckOut(contractId: string): Promise<Contract> {
  return apiFetch<Contract>(`/rental/contracts/${contractId}/check-out`, {
    method: "POST",
  });
}

export type ReturnSummary = {
  readonly contract: Contract;
  readonly baseRentalCents: number;
  readonly lateFeeCents: number;
  readonly damageFeeCents: number;
  readonly depositRefundCents: number;
  readonly netDueCents: number;
};

export async function processReturn(
  contractId: string,
  input: {
    readonly returnedAt?: string | null;
    readonly damageFeeCents?: number;
    readonly damageNotes?: string | null;
  } = {},
): Promise<ReturnSummary> {
  return apiFetch<ReturnSummary>(`/rental/contracts/${contractId}/return`, {
    method: "POST",
    json: {
      returnedAt: input.returnedAt ?? null,
      damageFeeCents: input.damageFeeCents ?? 0,
      damageNotes: input.damageNotes ?? null,
    },
  });
}
