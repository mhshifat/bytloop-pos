import { apiFetch } from "./fetcher";

export type SubscriptionStatus = "active" | "paused" | "expired";

export type MealPlan = {
  readonly id: string;
  readonly code: string;
  readonly name: string;
  readonly mealsPerPeriod: number;
  readonly periodDays: number;
  readonly priceCents: number;
  readonly createdAt: string;
};

export type Subscription = {
  readonly id: string;
  readonly customerId: string;
  readonly planCode: string;
  readonly mealsRemaining: number;
  readonly periodEndsOn: string;
  readonly autoRenew: boolean;
  readonly status: SubscriptionStatus;
  readonly createdAt: string;
};

export type Redemption = {
  readonly id: string;
  readonly subscriptionId: string;
  readonly orderId: string | null;
  readonly mealsUsed: number;
  readonly redeemedAt: string;
};

export type CreatePlanInput = {
  readonly code: string;
  readonly name: string;
  readonly mealsPerPeriod: number;
  readonly periodDays?: number;
  readonly priceCents?: number;
};

export async function createPlan(input: CreatePlanInput): Promise<MealPlan> {
  return apiFetch<MealPlan>("/cafeteria/plans", { method: "POST", json: input });
}

export async function listPlans(): Promise<readonly MealPlan[]> {
  return apiFetch<readonly MealPlan[]>("/cafeteria/plans");
}

export type SubscribeInput = {
  readonly customerId: string;
  readonly planCode: string;
  readonly startsOn: string;
  readonly autoRenew?: boolean;
};

export async function subscribe(input: SubscribeInput): Promise<Subscription> {
  return apiFetch<Subscription>("/cafeteria/subscriptions", {
    method: "POST",
    json: input,
  });
}

export async function listSubscriptions(
  customerId?: string,
): Promise<readonly Subscription[]> {
  const qs = customerId ? `?customerId=${encodeURIComponent(customerId)}` : "";
  return apiFetch<readonly Subscription[]>(`/cafeteria/subscriptions${qs}`);
}

export async function getSubscription(
  subscriptionId: string,
): Promise<Subscription> {
  return apiFetch<Subscription>(`/cafeteria/subscriptions/${subscriptionId}`);
}

export async function pauseSubscription(
  subscriptionId: string,
): Promise<Subscription> {
  return apiFetch<Subscription>(
    `/cafeteria/subscriptions/${subscriptionId}/pause`,
    { method: "POST" },
  );
}

export async function resumeSubscription(
  subscriptionId: string,
): Promise<Subscription> {
  return apiFetch<Subscription>(
    `/cafeteria/subscriptions/${subscriptionId}/resume`,
    { method: "POST" },
  );
}

export type RedeemInput = {
  readonly mealsUsed?: number;
  readonly orderId?: string | null;
};

export async function redeem(
  subscriptionId: string,
  input: RedeemInput = {},
): Promise<Redemption> {
  return apiFetch<Redemption>(
    `/cafeteria/subscriptions/${subscriptionId}/redeem`,
    { method: "POST", json: input },
  );
}

export async function listRedemptions(
  subscriptionId: string,
): Promise<readonly Redemption[]> {
  return apiFetch<readonly Redemption[]>(
    `/cafeteria/subscriptions/${subscriptionId}/redemptions`,
  );
}

export async function renewSubscription(
  subscriptionId: string,
): Promise<Subscription> {
  return apiFetch<Subscription>(
    `/cafeteria/subscriptions/${subscriptionId}/renew`,
    { method: "POST" },
  );
}
