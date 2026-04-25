import { apiFetch } from "./fetcher";

export type Campaign = {
  readonly id: string;
  readonly code: string;
  readonly name: string;
  readonly goalCents: number;
  readonly startsOn: string | null;
  readonly endsOn: string | null;
  readonly active: boolean;
};

export type Donation = {
  readonly id: string;
  readonly customerId: string | null;
  readonly amountCents: number;
  readonly currency: string;
  readonly campaign: string | null;
  readonly donorNameOverride: string | null;
  readonly isAnonymous: boolean;
  readonly taxDeductible: boolean;
  readonly receiptNo: string;
  readonly receivedAt: string;
};

export type CampaignTotals = {
  readonly code: string;
  readonly donationCount: number;
  readonly totalCents: number;
  readonly goalCents: number;
  readonly progressPct: number;
};

export type DonationReceipt = {
  readonly receiptNo: string;
  readonly donorName: string;
  readonly amountCents: number;
  readonly currency: string;
  readonly campaign: string | null;
  readonly taxDeductible: boolean;
  readonly receivedAt: string;
};

export async function listCampaigns(): Promise<readonly Campaign[]> {
  return apiFetch<readonly Campaign[]>("/donations/campaigns");
}

export async function createCampaign(input: {
  readonly code: string;
  readonly name: string;
  readonly goalCents?: number;
  readonly startsOn?: string | null;
  readonly endsOn?: string | null;
  readonly active?: boolean;
}): Promise<Campaign> {
  return apiFetch<Campaign>("/donations/campaigns", {
    method: "POST",
    json: {
      code: input.code,
      name: input.name,
      goalCents: input.goalCents ?? 0,
      startsOn: input.startsOn ?? null,
      endsOn: input.endsOn ?? null,
      active: input.active ?? true,
    },
  });
}

export async function listDonations(
  campaign?: string,
): Promise<readonly Donation[]> {
  const query = campaign ? `?campaign=${encodeURIComponent(campaign)}` : "";
  return apiFetch<readonly Donation[]>(`/donations${query}`);
}

export async function createDonation(input: {
  readonly customerId?: string | null;
  readonly amountCents: number;
  readonly currency?: string;
  readonly campaign?: string | null;
  readonly donorNameOverride?: string | null;
  readonly isAnonymous?: boolean;
  readonly taxDeductible?: boolean;
}): Promise<Donation> {
  return apiFetch<Donation>("/donations", {
    method: "POST",
    json: {
      customerId: input.customerId ?? null,
      amountCents: input.amountCents,
      currency: input.currency ?? "BDT",
      campaign: input.campaign ?? null,
      donorNameOverride: input.donorNameOverride ?? null,
      isAnonymous: input.isAnonymous ?? false,
      taxDeductible: input.taxDeductible ?? true,
    },
  });
}

export async function getDonation(donationId: string): Promise<Donation> {
  return apiFetch<Donation>(`/donations/${donationId}`);
}

export async function issueDonationReceipt(
  donationId: string,
): Promise<DonationReceipt> {
  return apiFetch<DonationReceipt>(`/donations/${donationId}/receipt`);
}

export async function getCampaignTotals(
  code: string,
): Promise<CampaignTotals> {
  return apiFetch<CampaignTotals>(
    `/donations/campaigns/${encodeURIComponent(code)}/totals`,
  );
}
