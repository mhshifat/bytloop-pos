import type { PurchaseOrderStatus } from "@/lib/api/procurement";

const LABELS: Record<PurchaseOrderStatus, string> = {
  draft: "Draft",
  sent: "Sent",
  partially_received: "Partially received",
  received: "Received",
  closed: "Closed",
  cancelled: "Cancelled",
};

export function purchaseOrderStatusLabel(status: PurchaseOrderStatus): string {
  return LABELS[status];
}
