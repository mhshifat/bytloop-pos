import { apiFetch } from "./fetcher";

export type LoyaltyCard = {
  readonly id: string;
  readonly customerId: string;
  readonly cardCode: string;
  readonly punchesCurrent: number;
  readonly punchesRequired: number;
  readonly freeItemsEarned: number;
  readonly totalPunchesLifetime: number;
};

export type PunchResponse = {
  readonly card: LoyaltyCard;
  readonly earnedThisPunch: boolean;
};

export async function listCardsForCustomer(
  customerId: string,
): Promise<readonly LoyaltyCard[]> {
  return apiFetch<readonly LoyaltyCard[]>(
    `/cafe-loyalty/cards?customerId=${encodeURIComponent(customerId)}`,
  );
}

export async function issueLoyaltyCard(input: {
  readonly customerId: string;
  readonly cardCode: string;
  readonly punchesRequired?: number;
}): Promise<LoyaltyCard> {
  return apiFetch<LoyaltyCard>("/cafe-loyalty/cards", {
    method: "POST",
    json: {
      customerId: input.customerId,
      cardCode: input.cardCode,
      punchesRequired: input.punchesRequired ?? 10,
    },
  });
}

export async function punchLoyaltyCard(input: {
  readonly cardCode: string;
  readonly count?: number;
}): Promise<PunchResponse> {
  return apiFetch<PunchResponse>("/cafe-loyalty/punch", {
    method: "POST",
    json: {
      cardCode: input.cardCode,
      count: input.count ?? 1,
    },
  });
}

export async function redeemLoyaltyFreeItem(
  cardCode: string,
): Promise<LoyaltyCard> {
  return apiFetch<LoyaltyCard>("/cafe-loyalty/redeem", {
    method: "POST",
    json: { cardCode },
  });
}
