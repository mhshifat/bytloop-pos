import { apiFetch } from "./fetcher";

export type MembershipStatus = "active" | "paused" | "expired" | "cancelled";

export type Membership = {
  readonly id: string;
  readonly customerId: string;
  readonly planCode: string;
  readonly status: MembershipStatus;
  readonly startsOn: string;
  readonly endsOn: string;
};

export async function listMemberships(): Promise<readonly Membership[]> {
  return apiFetch<readonly Membership[]>("/gym/memberships");
}

export async function createMembership(input: {
  readonly customerId: string;
  readonly planCode: string;
  readonly startsOn: string;
  readonly endsOn: string;
}): Promise<Membership> {
  return apiFetch<Membership>("/gym/memberships", { method: "POST", json: input });
}

export async function checkIn(membershipId: string): Promise<{ readonly id: string }> {
  return apiFetch<{ readonly id: string }>("/gym/checkins", {
    method: "POST",
    json: { membershipId },
  });
}

export type GymPlan = {
  readonly id: string;
  readonly code: string;
  readonly name: string;
  readonly durationDays: number;
  readonly priceCents: number;
  readonly isActive: boolean;
};

export async function listPlans(): Promise<readonly GymPlan[]> {
  return apiFetch<readonly GymPlan[]>("/gym/plans");
}

export async function upsertPlan(input: {
  readonly code: string;
  readonly name: string;
  readonly durationDays: number;
  readonly priceCents: number;
  readonly isActive: boolean;
}): Promise<GymPlan> {
  return apiFetch<GymPlan>("/gym/plans", { method: "PUT", json: input });
}

export async function createMembershipFromPlan(input: {
  readonly customerId: string;
  readonly planCode: string;
  readonly startsOn?: string | null;
}): Promise<Membership> {
  return apiFetch<Membership>("/gym/memberships/from-plan", {
    method: "POST",
    json: input,
  });
}

export type GymClass = {
  readonly id: string;
  readonly title: string;
  readonly trainerId: string | null;
  readonly startsAt: string;
  readonly endsAt: string;
  readonly capacity: number;
};

export async function listClasses(): Promise<readonly GymClass[]> {
  return apiFetch<readonly GymClass[]>("/gym/classes");
}

export async function scheduleClass(input: {
  readonly title: string;
  readonly trainerId?: string | null;
  readonly startsAt: string;
  readonly endsAt: string;
  readonly capacity: number;
}): Promise<GymClass> {
  return apiFetch<GymClass>("/gym/classes", { method: "POST", json: input });
}

export async function bookClass(
  classId: string,
  membershipId: string,
): Promise<{ readonly id: string }> {
  return apiFetch<{ readonly id: string }>(`/gym/classes/${classId}/bookings`, {
    method: "POST",
    json: { membershipId },
  });
}
