import { apiFetch } from "./fetcher";

export type CampaignTrigger = {
  readonly id: string;
  readonly segmentId: string | null;
  readonly channel: string;
  readonly threshold: number;
  readonly subject: string;
  readonly htmlTemplate: string;
  readonly discountCode: string | null;
  readonly cooldownDays: number;
  readonly enabled: boolean;
  readonly createdAt: string;
};

export async function listCampaignTriggers(): Promise<readonly CampaignTrigger[]> {
  return apiFetch<readonly CampaignTrigger[]>("/personalization/campaign-triggers");
}

export async function createCampaignTrigger(input: {
  readonly segmentId?: string | null;
  readonly threshold: number;
  readonly subject: string;
  readonly htmlTemplate: string;
  readonly discountCode?: string | null;
  readonly cooldownDays: number;
  readonly enabled: boolean;
}): Promise<CampaignTrigger> {
  return apiFetch<CampaignTrigger>("/personalization/campaign-triggers", { method: "POST", json: input });
}

