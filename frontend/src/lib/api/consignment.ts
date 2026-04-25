import { apiFetch } from "./fetcher";

export type ConsignmentItemStatus = "listed" | "sold" | "returned";

export type Consignor = {
  readonly id: string;
  readonly name: string;
  readonly email: string | null;
  readonly phone: string | null;
  readonly payoutRatePct: number;
  readonly balanceCents: number;
  readonly createdAt: string;
};

export type ConsignmentItem = {
  readonly id: string;
  readonly consignorId: string;
  readonly productId: string;
  readonly status: ConsignmentItemStatus;
  readonly listedPriceCents: number;
  readonly listedAt: string;
  readonly soldAt: string | null;
  readonly soldPriceCents: number | null;
  readonly consignorShareCents: number | null;
  readonly soldOrderId: string | null;
};

export type ConsignorPayout = {
  readonly id: string;
  readonly consignorId: string;
  readonly amountCents: number;
  readonly balanceAfterCents: number;
  readonly note: string | null;
  readonly createdAt: string;
};

export async function listConsignors(): Promise<readonly Consignor[]> {
  return apiFetch<readonly Consignor[]>("/consignment/consignors");
}

export type CreateConsignorInput = {
  readonly name: string;
  readonly email?: string | null;
  readonly phone?: string | null;
  readonly payoutRatePct?: number;
};

export async function createConsignor(
  input: CreateConsignorInput,
): Promise<Consignor> {
  return apiFetch<Consignor>("/consignment/consignors", {
    method: "POST",
    json: input,
  });
}

export async function listItems(params: {
  readonly consignorId?: string;
  readonly status?: ConsignmentItemStatus;
} = {}): Promise<readonly ConsignmentItem[]> {
  const sp = new URLSearchParams();
  if (params.consignorId) sp.set("consignorId", params.consignorId);
  if (params.status) sp.set("status", params.status);
  const qs = sp.toString();
  return apiFetch<readonly ConsignmentItem[]>(
    `/consignment/items${qs ? `?${qs}` : ""}`,
  );
}

export type AddItemInput = {
  readonly consignorId: string;
  readonly productId: string;
  readonly listedPriceCents: number;
};

export async function addItem(input: AddItemInput): Promise<ConsignmentItem> {
  return apiFetch<ConsignmentItem>("/consignment/items", {
    method: "POST",
    json: input,
  });
}

export async function markItemSold(
  itemId: string,
  input: { readonly soldPriceCents: number; readonly orderId: string },
): Promise<ConsignmentItem> {
  return apiFetch<ConsignmentItem>(`/consignment/items/${itemId}/mark-sold`, {
    method: "POST",
    json: input,
  });
}

export async function returnItem(itemId: string): Promise<ConsignmentItem> {
  return apiFetch<ConsignmentItem>(`/consignment/items/${itemId}/return`, {
    method: "POST",
  });
}

export async function createPayout(
  consignorId: string,
  input: { readonly amountCents: number; readonly note?: string | null },
): Promise<ConsignorPayout> {
  return apiFetch<ConsignorPayout>(
    `/consignment/consignors/${consignorId}/payouts`,
    { method: "POST", json: input },
  );
}

export async function listPayouts(
  consignorId: string,
): Promise<readonly ConsignorPayout[]> {
  return apiFetch<readonly ConsignorPayout[]>(
    `/consignment/consignors/${consignorId}/payouts`,
  );
}
