import { apiFetch } from "./fetcher";

export type Batch = {
  readonly id: string;
  readonly productId: string;
  readonly batchNo: string;
  readonly expiryDate: string;
  readonly quantityRemaining: number;
};

export async function listBatches(productId?: string): Promise<readonly Batch[]> {
  const sp = new URLSearchParams();
  if (productId) sp.set("productId", productId);
  const q = sp.toString();
  return apiFetch<readonly Batch[]>(`/pharmacy/batches${q ? `?${q}` : ""}`);
}

export async function listExpiringBatches(days = 30): Promise<readonly Batch[]> {
  return apiFetch<readonly Batch[]>(`/pharmacy/batches/expiring?days=${days}`);
}

export type BatchCreateInput = {
  readonly productId: string;
  readonly batchNo: string;
  readonly expiryDate: string;
  readonly quantity: number;
};

export async function createBatch(input: BatchCreateInput): Promise<Batch> {
  return apiFetch<Batch>("/pharmacy/batches", { method: "POST", json: input });
}

export type DrugMetadata = {
  readonly productId: string;
  readonly isControlled: boolean;
  readonly schedule: string | null;
  readonly dosageForm: string | null;
  readonly strength: string | null;
};

export async function upsertDrugMetadata(input: {
  readonly productId: string;
  readonly isControlled: boolean;
  readonly schedule?: string | null;
  readonly dosageForm?: string | null;
  readonly strength?: string | null;
}): Promise<DrugMetadata> {
  return apiFetch<DrugMetadata>("/pharmacy/drug-metadata", {
    method: "PUT",
    json: input,
  });
}

export type Prescription = {
  readonly id: string;
  readonly customerId: string | null;
  readonly orderId: string | null;
  readonly prescriptionNo: string;
  readonly doctorName: string;
  readonly doctorLicense: string | null;
  readonly issuedOn: string;
  readonly notes: string | null;
};

export async function createPrescription(input: {
  readonly customerId?: string | null;
  readonly prescriptionNo: string;
  readonly doctorName: string;
  readonly doctorLicense?: string | null;
  readonly issuedOn: string;
  readonly notes?: string | null;
}): Promise<Prescription> {
  return apiFetch<Prescription>("/pharmacy/prescriptions", {
    method: "POST",
    json: input,
  });
}

export async function listPrescriptions(
  customerId?: string,
): Promise<readonly Prescription[]> {
  const sp = new URLSearchParams();
  if (customerId) sp.set("customerId", customerId);
  const q = sp.toString();
  return apiFetch<readonly Prescription[]>(
    `/pharmacy/prescriptions${q ? `?${q}` : ""}`,
  );
}

export type FefoLine = {
  readonly batchId: string;
  readonly batchNo: string;
  readonly quantity: number;
};

export async function fefoDispatch(input: {
  readonly productId: string;
  readonly quantity: number;
  readonly prescriptionId?: string | null;
}): Promise<readonly FefoLine[]> {
  return apiFetch<readonly FefoLine[]>("/pharmacy/fefo-dispatch", {
    method: "POST",
    json: input,
  });
}
