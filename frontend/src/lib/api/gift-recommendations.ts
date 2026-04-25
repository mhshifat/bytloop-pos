import { apiFetch } from "./fetcher";

export type GiftRecommendationRequest = {
  readonly prompt: string;
  readonly budgetCents: number;
  readonly currency: string;
  readonly verticalHint?: string | null;
};

export type GiftRecommendation = {
  readonly productId: string;
  readonly rationale: string;
};

export async function giftRecommendations(
  input: GiftRecommendationRequest,
): Promise<{ readonly products: readonly GiftRecommendation[] }> {
  return apiFetch("/personalization/gift-recommendations", { method: "POST", json: input });
}

