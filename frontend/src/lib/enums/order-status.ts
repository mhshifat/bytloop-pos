import type { OrderRead } from "@/lib/api/sales";

type OrderStatus = OrderRead["status"];
type OrderType = OrderRead["orderType"];

const STATUS_LABELS: Record<OrderStatus, string> = {
  open: "Open",
  completed: "Completed",
  voided: "Voided",
  refunded: "Refunded",
};

const TYPE_LABELS: Record<OrderType, string> = {
  retail: "Retail",
  dine_in: "Dine-in",
  takeaway: "Takeaway",
  delivery: "Delivery",
  appointment: "Appointment",
  job_card: "Job card",
  rental: "Rental",
};

export function orderStatusLabel(status: OrderStatus): string {
  return STATUS_LABELS[status];
}

export function orderTypeLabel(type: OrderType): string {
  return TYPE_LABELS[type];
}
