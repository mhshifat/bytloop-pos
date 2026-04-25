import { apiFetch } from "./fetcher";

export type AuditEvent = {
  readonly id: string;
  readonly actorId: string | null;
  readonly action: string;
  readonly resourceType: string;
  readonly resourceId: string | null;
  readonly before: unknown;
  readonly after: unknown;
  readonly correlationId: string | null;
  readonly createdAt: string;
};

export type AuditEventList = {
  readonly items: readonly AuditEvent[];
  readonly hasMore: boolean;
  readonly page: number;
  readonly pageSize: number;
};

export async function listAudit(params: {
  readonly resourceType?: string;
  readonly page?: number;
  readonly pageSize?: number;
} = {}): Promise<AuditEventList> {
  const sp = new URLSearchParams();
  if (params.resourceType) sp.set("resourceType", params.resourceType);
  if (params.page) sp.set("page", String(params.page));
  if (params.pageSize) sp.set("pageSize", String(params.pageSize));
  const q = sp.toString();
  return apiFetch<AuditEventList>(`/audit${q ? `?${q}` : ""}`);
}
