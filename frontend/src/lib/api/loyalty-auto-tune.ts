import { apiFetch } from "./fetcher";

export type LoyaltyAutoTune = {
  readonly totalCards: number;
  readonly currentPunchesRequired: number;
  readonly recommendedPunchesRequired: number;
  readonly earnedRate: number;
  readonly reason: string;
};

export async function getLoyaltyAutoTune(): Promise<LoyaltyAutoTune> {
  return apiFetch("/personalization/loyalty/auto-tune");
}

export async function applyLoyaltyAutoTune(input: { readonly punchesRequired: number }): Promise<{
  readonly ok: boolean;
  readonly updated?: number;
  readonly punchesRequired?: number;
  readonly error?: string;
}> {
  return apiFetch("/personalization/loyalty/apply", { method: "POST", json: input });
}

