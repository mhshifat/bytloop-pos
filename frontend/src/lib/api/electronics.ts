import { apiFetch } from "./fetcher";

export type ElectronicsItem = {
  readonly id: string;
  readonly productId: string;
  readonly serialNo: string;
  readonly imei: string | null;
  readonly warrantyMonths: number;
  readonly purchasedOn: string | null;
  readonly soldOrderId: string | null;
  readonly soldAt: string | null;
};

export type WarrantyStatus = {
  readonly serialNo: string;
  readonly covered: boolean;
  readonly daysRemaining: number;
  readonly warrantyExpiresOn: string | null;
};

export async function listItems(productId: string): Promise<readonly ElectronicsItem[]> {
  return apiFetch<readonly ElectronicsItem[]>(
    `/electronics/items?productId=${encodeURIComponent(productId)}`,
  );
}

export type RegisterItemInput = {
  readonly productId: string;
  readonly serialNo: string;
  readonly imei?: string | null;
  readonly warrantyMonths?: number;
  readonly purchasedOn?: string | null;
};

export async function registerItem(input: RegisterItemInput): Promise<ElectronicsItem> {
  return apiFetch<ElectronicsItem>("/electronics/items", {
    method: "POST",
    json: input,
  });
}

export async function lookupItem(params: {
  readonly serial?: string;
  readonly imei?: string;
}): Promise<ElectronicsItem> {
  const sp = new URLSearchParams();
  if (params.serial) sp.set("serial", params.serial);
  if (params.imei) sp.set("imei", params.imei);
  return apiFetch<ElectronicsItem>(`/electronics/lookup?${sp.toString()}`);
}

export async function markItemSold(
  itemId: string,
  orderId: string,
): Promise<ElectronicsItem> {
  return apiFetch<ElectronicsItem>(`/electronics/items/${itemId}/mark-sold`, {
    method: "POST",
    json: { orderId },
  });
}

export async function warrantyStatus(serial: string): Promise<WarrantyStatus> {
  return apiFetch<WarrantyStatus>(
    `/electronics/warranty?serial=${encodeURIComponent(serial)}`,
  );
}
