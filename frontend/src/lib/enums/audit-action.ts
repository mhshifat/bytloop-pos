/**
 * Human labels for audit event actions. The raw dotted identifiers
 * (`staff.invited`, `order.voided`, …) must never be surfaced as UI text —
 * they are a system contract, not end-user copy.
 */

const LABELS: Record<string, string> = {
  "customer.created": "Customer created",
  "product.created": "Product created",
  "product.updated": "Product updated",
  "product.deleted": "Product deleted",
  "order.completed": "Order completed",
  "order.voided": "Order voided",
  "order.refunded": "Order refunded",
  "purchase_order.created": "Purchase order created",
  "purchase_order.received": "Purchase order received",
  "supplier.created": "Supplier created",
  "user.signup": "Signed up",
  "user.email_verified": "Email verified",
  "user.password_changed": "Password changed",
  "staff.invited": "Staff invited",
  "staff.roles_updated": "Staff roles updated",
  "staff.removed": "Staff removed",
};

export function auditActionLabel(action: string): string {
  if (LABELS[action]) return LABELS[action];
  // Unknown actions: humanize the dotted identifier rather than leak it raw.
  return action
    .split(".")
    .map((part) => part.replace(/_/g, " "))
    .join(" · ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function resourceTypeLabel(resourceType: string): string {
  const map: Record<string, string> = {
    customer: "Customer",
    product: "Product",
    order: "Order",
    purchase_order: "Purchase order",
    supplier: "Supplier",
    user: "User",
    staff: "Staff",
    tenant: "Workspace",
  };
  return map[resourceType] ?? resourceType.replace(/_/g, " ");
}
