import { apiFetch } from "./fetcher";

export type Segment = {
  readonly id: string;
  readonly name: string;
  readonly kind: string;
  readonly createdAt: string;
};

export async function listSegments(): Promise<readonly Segment[]> {
  return apiFetch<readonly Segment[]>("/personalization/segments");
}

export async function recomputeSegments(): Promise<{
  readonly segmentsCreated: number;
  readonly membershipsWritten: number;
}> {
  return apiFetch("/personalization/segments/recompute", { method: "POST", json: {} });
}

export type SegmentMember = {
  readonly customerId: string;
  readonly score: number;
  readonly refreshedAt: string;
  readonly meta: Record<string, unknown>;
};

export async function listSegmentMembers(segmentId: string): Promise<readonly SegmentMember[]> {
  return apiFetch<readonly SegmentMember[]>(`/personalization/segments/${segmentId}/members`);
}

