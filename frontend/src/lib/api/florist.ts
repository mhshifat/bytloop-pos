import { apiFetch } from "./fetcher";

export type BouquetTemplate = {
  readonly id: string;
  readonly code: string;
  readonly name: string;
  readonly basePriceCents: number;
  readonly createdAt: string;
};

export type BouquetComponent = {
  readonly id: string;
  readonly templateId: string;
  readonly componentName: string;
  readonly defaultQuantity: number;
  readonly unitPriceCents: number;
};

export type BouquetInstance = {
  readonly id: string;
  readonly totalPriceCents: number;
  readonly templateId: string | null;
  readonly orderId: string | null;
  readonly wrapStyle: string | null;
  readonly cardMessage: string | null;
  readonly deliveryScheduleId: string | null;
  readonly createdAt: string;
};

export type BouquetInstanceItem = {
  readonly id: string;
  readonly instanceId: string;
  readonly componentName: string;
  readonly quantity: number;
  readonly unitPriceCents: number;
};

export async function listTemplates(): Promise<readonly BouquetTemplate[]> {
  return apiFetch<readonly BouquetTemplate[]>("/florist/templates");
}

export type CreateTemplateInput = {
  readonly code: string;
  readonly name: string;
  readonly basePriceCents: number;
};

export async function createTemplate(
  input: CreateTemplateInput,
): Promise<BouquetTemplate> {
  return apiFetch<BouquetTemplate>("/florist/templates", {
    method: "POST",
    json: input,
  });
}

export async function listComponents(
  templateId: string,
): Promise<readonly BouquetComponent[]> {
  return apiFetch<readonly BouquetComponent[]>(
    `/florist/templates/${templateId}/components`,
  );
}

export type AddComponentInput = {
  readonly templateId: string;
  readonly componentName: string;
  readonly defaultQuantity: number;
  readonly unitPriceCents: number;
};

export async function addComponent(
  input: AddComponentInput,
): Promise<BouquetComponent> {
  return apiFetch<BouquetComponent>("/florist/components", {
    method: "POST",
    json: input,
  });
}

export async function listInstances(): Promise<readonly BouquetInstance[]> {
  return apiFetch<readonly BouquetInstance[]>("/florist/instances");
}

export type ComposeItemInput = {
  readonly componentName: string;
  readonly quantity: number;
  readonly unitPriceCents: number;
};

export type ComposeInput = {
  readonly templateId?: string | null;
  readonly items?: readonly ComposeItemInput[] | null;
  readonly wrapStyle?: string | null;
  readonly cardMessage?: string | null;
  readonly deliveryScheduleId?: string | null;
};

export async function composeInstance(
  input: ComposeInput,
): Promise<BouquetInstance> {
  return apiFetch<BouquetInstance>("/florist/instances", {
    method: "POST",
    json: input,
  });
}

export async function getInstance(
  instanceId: string,
): Promise<BouquetInstance> {
  return apiFetch<BouquetInstance>(`/florist/instances/${instanceId}`);
}

export async function listInstanceItems(
  instanceId: string,
): Promise<readonly BouquetInstanceItem[]> {
  return apiFetch<readonly BouquetInstanceItem[]>(
    `/florist/instances/${instanceId}/items`,
  );
}

export async function linkOrder(
  instanceId: string,
  orderId: string,
): Promise<BouquetInstance> {
  return apiFetch<BouquetInstance>(
    `/florist/instances/${instanceId}/link-order`,
    { method: "POST", json: { orderId } },
  );
}
