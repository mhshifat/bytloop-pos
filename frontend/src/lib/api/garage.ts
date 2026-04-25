import { apiFetch } from "./fetcher";

export type Vehicle = {
  readonly id: string;
  readonly plate: string;
  readonly make: string;
  readonly model: string;
  readonly year: number | null;
  readonly vin: string | null;
  readonly customerId: string | null;
};

export type JobCardStatus = "open" | "in_progress" | "completed" | "delivered";

export type JobCard = {
  readonly id: string;
  readonly vehicleId: string;
  readonly technicianId: string | null;
  readonly status: JobCardStatus;
  readonly description: string;
  readonly orderId: string | null;
};

export async function listVehicles(): Promise<readonly Vehicle[]> {
  return apiFetch<readonly Vehicle[]>("/garage/vehicles");
}

export async function registerVehicle(input: {
  readonly plate: string;
  readonly make: string;
  readonly model: string;
  readonly year?: number | null;
  readonly vin?: string | null;
  readonly customerId?: string | null;
}): Promise<Vehicle> {
  return apiFetch<Vehicle>("/garage/vehicles", { method: "POST", json: input });
}

export async function listJobs(): Promise<readonly JobCard[]> {
  return apiFetch<readonly JobCard[]>("/garage/jobs");
}

export async function openJob(input: {
  readonly vehicleId: string;
  readonly description: string;
  readonly technicianId?: string | null;
}): Promise<JobCard> {
  return apiFetch<JobCard>("/garage/jobs", { method: "POST", json: input });
}

export async function updateJobStatus(
  jobId: string,
  status: JobCardStatus,
): Promise<JobCard> {
  return apiFetch<JobCard>(`/garage/jobs/${jobId}/status`, {
    method: "PATCH",
    json: { status },
  });
}

export type JobLineKind = "part" | "labor";

export type JobLine = {
  readonly id: string;
  readonly jobCardId: string;
  readonly kind: JobLineKind;
  readonly productId: string | null;
  readonly description: string;
  readonly quantity: number;
  readonly unitCostCents: number;
  readonly lineTotalCents: number;
  readonly createdAt: string;
};

export async function listJobLines(jobId: string): Promise<readonly JobLine[]> {
  return apiFetch<readonly JobLine[]>(`/garage/jobs/${jobId}/lines`);
}

export async function addJobLine(
  jobId: string,
  input: {
    readonly kind: JobLineKind;
    readonly description: string;
    readonly quantity: number;
    readonly unitCostCents: number;
    readonly productId?: string | null;
  },
): Promise<JobLine> {
  return apiFetch<JobLine>(`/garage/jobs/${jobId}/lines`, {
    method: "POST",
    json: input,
  });
}

export async function removeJobLine(jobId: string, lineId: string): Promise<void> {
  return apiFetch<void>(`/garage/jobs/${jobId}/lines/${lineId}`, {
    method: "DELETE",
  });
}

export type JobTotals = {
  readonly partsCents: number;
  readonly laborCents: number;
  readonly totalCents: number;
};

export async function getJobTotals(jobId: string): Promise<JobTotals> {
  return apiFetch<JobTotals>(`/garage/jobs/${jobId}/totals`);
}

export type VehicleHistoryItem = {
  readonly id: string;
  readonly status: JobCardStatus;
  readonly description: string;
  readonly openedAt: string;
  readonly closedAt: string | null;
};

export async function getVehicleHistory(
  vehicleId: string,
): Promise<readonly VehicleHistoryItem[]> {
  return apiFetch<readonly VehicleHistoryItem[]>(
    `/garage/vehicles/${vehicleId}/history`,
  );
}
