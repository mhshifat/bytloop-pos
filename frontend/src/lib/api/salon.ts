import { apiFetch } from "./fetcher";

export type AppointmentStatus =
  | "booked"
  | "checked_in"
  | "completed"
  | "no_show"
  | "cancelled";

export type Appointment = {
  readonly id: string;
  readonly customerId: string;
  readonly staffId: string | null;
  readonly serviceId: string | null;
  readonly serviceName: string;
  readonly status: AppointmentStatus;
  readonly startsAt: string;
  readonly endsAt: string;
  readonly orderId: string | null;
};

export async function listAppointments(days = 7): Promise<readonly Appointment[]> {
  return apiFetch<readonly Appointment[]>(`/salon/appointments?days=${days}`);
}

export async function bookAppointment(input: {
  readonly customerId: string;
  readonly staffId?: string | null;
  readonly serviceId?: string | null;
  readonly serviceName: string;
  readonly startsAt: string;
  readonly endsAt: string;
}): Promise<Appointment> {
  return apiFetch<Appointment>("/salon/appointments", { method: "POST", json: input });
}

export async function updateAppointmentStatus(
  id: string,
  status: AppointmentStatus,
): Promise<Appointment> {
  return apiFetch<Appointment>(`/salon/appointments/${id}/status`, {
    method: "PATCH",
    json: { status },
  });
}

export type SalonService = {
  readonly id: string;
  readonly code: string;
  readonly name: string;
  readonly durationMinutes: number;
  readonly priceCents: number;
  readonly isActive: boolean;
  readonly productId: string | null;
};

export async function listSalonServices(): Promise<readonly SalonService[]> {
  return apiFetch<readonly SalonService[]>("/salon/services");
}

export async function upsertSalonService(input: {
  readonly code: string;
  readonly name: string;
  readonly durationMinutes: number;
  readonly priceCents: number;
  readonly productId?: string | null;
  readonly isActive: boolean;
}): Promise<SalonService> {
  return apiFetch<SalonService>("/salon/services", { method: "PUT", json: input });
}

export type AvailabilityWindow = {
  readonly startsAt: string;
  readonly endsAt: string;
};

export async function stylistAvailability(
  staffId: string,
  date: string,
): Promise<readonly AvailabilityWindow[]> {
  return apiFetch<readonly AvailabilityWindow[]>(
    `/salon/stylists/${staffId}/availability?date=${date}`,
  );
}

export async function checkInAppointment(
  appointmentId: string,
): Promise<{ appointment: Appointment; productId: string | null }> {
  return apiFetch<{ appointment: Appointment; productId: string | null }>(
    `/salon/appointments/${appointmentId}/check-in`,
    { method: "POST" },
  );
}
