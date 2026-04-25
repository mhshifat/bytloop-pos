import { apiFetch } from "./fetcher";

export type BarTabStatus = "open" | "closed" | "abandoned";

export type BarTabLine = {
  readonly id: string;
  readonly productId: string;
  readonly quantity: number;
  readonly unitPriceCents: number;
  readonly addedAt: string;
};

export type BarTab = {
  readonly id: string;
  readonly customerId: string | null;
  readonly status: BarTabStatus;
  readonly preauthReference: string | null;
  readonly openedAt: string;
  readonly closedAt: string | null;
  readonly orderId: string | null;
  readonly totalCents: number;
  readonly lines: readonly BarTabLine[];
};

export async function openBarTab(input: {
  readonly customerId?: string | null;
  readonly preauthReference?: string | null;
}): Promise<BarTab> {
  return apiFetch<BarTab>("/bar-tabs", {
    method: "POST",
    json: {
      customerId: input.customerId ?? null,
      preauthReference: input.preauthReference ?? null,
    },
  });
}

export async function listOpenBarTabs(): Promise<readonly BarTab[]> {
  return apiFetch<readonly BarTab[]>("/bar-tabs");
}

export async function getBarTab(tabId: string): Promise<BarTab> {
  return apiFetch<BarTab>(`/bar-tabs/${tabId}`);
}

export async function addBarTabLine(
  tabId: string,
  input: {
    readonly productId: string;
    readonly quantity?: number;
    readonly unitPriceCents: number;
  },
): Promise<BarTab> {
  return apiFetch<BarTab>(`/bar-tabs/${tabId}/lines`, {
    method: "POST",
    json: {
      productId: input.productId,
      quantity: input.quantity ?? 1,
      unitPriceCents: input.unitPriceCents,
    },
  });
}

export async function closeBarTab(tabId: string): Promise<BarTab> {
  return apiFetch<BarTab>(`/bar-tabs/${tabId}/close`, {
    method: "POST",
    json: {},
  });
}

export async function abandonBarTab(tabId: string): Promise<BarTab> {
  return apiFetch<BarTab>(`/bar-tabs/${tabId}/abandon`, { method: "POST" });
}
