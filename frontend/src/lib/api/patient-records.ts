import { apiFetch } from "./fetcher";

export type PatientKind = "person" | "pet";

export type Patient = {
  readonly id: string;
  readonly customerId: string | null;
  readonly kind: PatientKind;
  readonly firstName: string | null;
  readonly petName: string | null;
  readonly dobOrBirthYear: string | null;
  readonly species: string | null;
  readonly breed: string | null;
  readonly allergies: string | null;
  readonly notes: string | null;
};

export type PatientCreateInput = {
  readonly customerId?: string | null;
  readonly kind: PatientKind;
  readonly firstName?: string | null;
  readonly petName?: string | null;
  readonly dobOrBirthYear?: string | null;
  readonly species?: string | null;
  readonly breed?: string | null;
  readonly allergies?: string | null;
  readonly notes?: string | null;
};

export async function listPatients(
  search?: string,
): Promise<readonly Patient[]> {
  const sp = new URLSearchParams();
  if (search) sp.set("search", search);
  const q = sp.toString();
  return apiFetch<readonly Patient[]>(
    `/patient-records/patients${q ? `?${q}` : ""}`,
  );
}

export async function getPatient(patientId: string): Promise<Patient> {
  return apiFetch<Patient>(`/patient-records/patients/${patientId}`);
}

export async function registerPatient(
  input: PatientCreateInput,
): Promise<Patient> {
  return apiFetch<Patient>("/patient-records/patients", {
    method: "POST",
    json: input,
  });
}

export type Visit = {
  readonly id: string;
  readonly patientId: string;
  readonly attendingUserId: string | null;
  readonly visitDate: string;
  readonly chiefComplaint: string;
  readonly diagnosis: string | null;
  readonly treatmentNotes: string | null;
  readonly orderId: string | null;
  readonly followUpOn: string | null;
  readonly createdAt: string;
};

export type VisitCreateInput = {
  readonly patientId: string;
  readonly attendingUserId?: string | null;
  readonly visitDate: string;
  readonly chiefComplaint: string;
  readonly diagnosis?: string | null;
  readonly treatmentNotes?: string | null;
  readonly orderId?: string | null;
  readonly followUpOn?: string | null;
};

export async function createVisit(input: VisitCreateInput): Promise<Visit> {
  return apiFetch<Visit>("/patient-records/visits", {
    method: "POST",
    json: input,
  });
}

export async function visitHistory(
  patientId: string,
): Promise<readonly Visit[]> {
  return apiFetch<readonly Visit[]>(
    `/patient-records/patients/${patientId}/visits`,
  );
}

export type Prescription = {
  readonly id: string;
  readonly patientId: string;
  readonly visitId: string | null;
  readonly medicationName: string;
  readonly dosage: string;
  readonly frequency: string;
  readonly durationDays: number;
  readonly prescribedByUserId: string | null;
  readonly createdAt: string;
};

export type PrescriptionCreateInput = {
  readonly patientId: string;
  readonly visitId?: string | null;
  readonly medicationName: string;
  readonly dosage: string;
  readonly frequency: string;
  readonly durationDays?: number;
};

export async function addPrescription(
  input: PrescriptionCreateInput,
): Promise<Prescription> {
  return apiFetch<Prescription>("/patient-records/prescriptions", {
    method: "POST",
    json: input,
  });
}

export async function listPatientPrescriptions(
  patientId: string,
): Promise<readonly Prescription[]> {
  return apiFetch<readonly Prescription[]>(
    `/patient-records/patients/${patientId}/prescriptions`,
  );
}
