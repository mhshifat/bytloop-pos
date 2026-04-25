import { apiFetch } from "./fetcher";

export async function getPairings(input: {
  readonly foodProductId: string;
}): Promise<{ readonly suggestedDrinkProductIds: readonly string[]; readonly rationale: string }> {
  return apiFetch("/personalization/pairings", { method: "POST", json: input });
}

