import { apiFetch } from "./fetcher";

export type DeliveryStatus =
  | "scheduled"
  | "out_for_delivery"
  | "delivered"
  | "failed";

export type DeliverySchedule = {
  readonly id: string;
  readonly orderId: string;
  readonly addressLine1: string;
  readonly addressLine2: string | null;
  readonly city: string;
  readonly postalCode: string;
  readonly country: string;
  readonly recipientName: string;
  readonly recipientPhone: string;
  readonly scheduledFor: string | null;
  readonly deliveredAt: string | null;
  readonly deliveryFeeCents: number;
  readonly status: DeliveryStatus;
  readonly notes: string | null;
};

export type ScheduleDeliveryInput = {
  readonly orderId: string;
  readonly addressLine1: string;
  readonly addressLine2?: string | null;
  readonly city: string;
  readonly postalCode: string;
  readonly country: string;
  readonly recipientName: string;
  readonly recipientPhone: string;
  readonly scheduledFor?: string | null;
  readonly deliveryFeeCents?: number;
  readonly notes?: string | null;
};

export async function scheduleDelivery(
  input: ScheduleDeliveryInput,
): Promise<DeliverySchedule> {
  return apiFetch<DeliverySchedule>("/deliveries", {
    method: "POST",
    json: input,
  });
}

export async function listScheduledDeliveries(
  day: string,
): Promise<readonly DeliverySchedule[]> {
  return apiFetch<readonly DeliverySchedule[]>(
    `/deliveries/scheduled?day=${day}`,
  );
}

export async function listDeliveriesForOrder(
  orderId: string,
): Promise<readonly DeliverySchedule[]> {
  return apiFetch<readonly DeliverySchedule[]>(
    `/deliveries/by-order/${orderId}`,
  );
}

export async function getDelivery(
  deliveryId: string,
): Promise<DeliverySchedule> {
  return apiFetch<DeliverySchedule>(`/deliveries/${deliveryId}`);
}

export async function markOutForDelivery(
  deliveryId: string,
): Promise<DeliverySchedule> {
  return apiFetch<DeliverySchedule>(
    `/deliveries/${deliveryId}/out-for-delivery`,
    { method: "POST" },
  );
}

export async function markDelivered(
  deliveryId: string,
): Promise<DeliverySchedule> {
  return apiFetch<DeliverySchedule>(`/deliveries/${deliveryId}/delivered`, {
    method: "POST",
  });
}

export async function markDeliveryFailed(
  deliveryId: string,
  reason: string,
): Promise<DeliverySchedule> {
  return apiFetch<DeliverySchedule>(`/deliveries/${deliveryId}/failed`, {
    method: "POST",
    json: { reason },
  });
}
