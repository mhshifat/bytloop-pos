import { apiFetch } from "./fetcher";

export type ModifierOption = {
  readonly id: string;
  readonly groupId: string;
  readonly name: string;
  readonly priceCentsDelta: number;
  readonly isDefault: boolean;
};

export type ModifierGroup = {
  readonly id: string;
  readonly code: string;
  readonly name: string;
  readonly minSelections: number;
  readonly maxSelections: number;
  readonly required: boolean;
  readonly options: readonly ModifierOption[];
};

export async function listModifierGroups(): Promise<readonly ModifierGroup[]> {
  return apiFetch<readonly ModifierGroup[]>("/modifiers/groups");
}

export async function createModifierGroup(input: {
  readonly code: string;
  readonly name: string;
  readonly minSelections?: number;
  readonly maxSelections?: number;
  readonly required?: boolean;
}): Promise<ModifierGroup> {
  return apiFetch<ModifierGroup>("/modifiers/groups", {
    method: "POST",
    json: input,
  });
}

export async function updateModifierGroup(
  groupId: string,
  input: {
    readonly name?: string;
    readonly minSelections?: number;
    readonly maxSelections?: number;
    readonly required?: boolean;
  },
): Promise<ModifierGroup> {
  return apiFetch<ModifierGroup>(`/modifiers/groups/${groupId}`, {
    method: "PATCH",
    json: input,
  });
}

export async function deleteModifierGroup(groupId: string): Promise<void> {
  return apiFetch<void>(`/modifiers/groups/${groupId}`, { method: "DELETE" });
}

export async function listModifierOptions(
  groupId: string,
): Promise<readonly ModifierOption[]> {
  return apiFetch<readonly ModifierOption[]>(
    `/modifiers/groups/${groupId}/options`,
  );
}

export async function createModifierOption(
  groupId: string,
  input: {
    readonly name: string;
    readonly priceCentsDelta?: number;
    readonly isDefault?: boolean;
  },
): Promise<ModifierOption> {
  return apiFetch<ModifierOption>(`/modifiers/groups/${groupId}/options`, {
    method: "POST",
    json: input,
  });
}

export async function updateModifierOption(
  optionId: string,
  input: {
    readonly name?: string;
    readonly priceCentsDelta?: number;
    readonly isDefault?: boolean;
  },
): Promise<ModifierOption> {
  return apiFetch<ModifierOption>(`/modifiers/options/${optionId}`, {
    method: "PATCH",
    json: input,
  });
}

export async function deleteModifierOption(optionId: string): Promise<void> {
  return apiFetch<void>(`/modifiers/options/${optionId}`, { method: "DELETE" });
}

export async function listGroupsForProduct(
  productId: string,
): Promise<readonly ModifierGroup[]> {
  return apiFetch<readonly ModifierGroup[]>(
    `/modifiers/products/${productId}/groups`,
  );
}

export async function attachGroupToProduct(
  productId: string,
  modifierGroupId: string,
): Promise<ModifierGroup> {
  return apiFetch<ModifierGroup>(`/modifiers/products/${productId}/groups`, {
    method: "POST",
    json: { modifierGroupId },
  });
}

export async function detachGroupFromProduct(
  productId: string,
  groupId: string,
): Promise<void> {
  return apiFetch<void>(
    `/modifiers/products/${productId}/groups/${groupId}`,
    { method: "DELETE" },
  );
}

export type PriceLineResponse = {
  readonly productId: string;
  readonly basePriceCents: number;
  readonly modifierDeltaCents: number;
  readonly totalCents: number;
};

export async function priceLine(input: {
  readonly productId: string;
  readonly optionIds: readonly string[];
}): Promise<PriceLineResponse> {
  return apiFetch<PriceLineResponse>("/modifiers/price-line", {
    method: "POST",
    json: input,
  });
}
