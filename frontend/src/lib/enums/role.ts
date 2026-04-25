import { Role } from "@/lib/rbac";

const LABELS: Record<Role, string> = {
  owner: "Owner",
  manager: "Manager",
  cashier: "Cashier",
  kitchen: "Kitchen",
  staff: "Staff",
};

const DESCRIPTIONS: Record<Role, string> = {
  owner: "Full access, including billing and ownership",
  manager: "Manage catalog, staff, reports, refunds and voids",
  cashier: "Ring up sales at the POS terminal",
  kitchen: "Work the kitchen display, mark items ready",
  staff: "Read-only catalog access",
};

export function roleLabel(role: string): string {
  return LABELS[role as Role] ?? role;
}

export function roleDescription(role: string): string {
  return DESCRIPTIONS[role as Role] ?? "";
}

export const ALL_ROLES: readonly Role[] = [
  Role.OWNER,
  Role.MANAGER,
  Role.CASHIER,
  Role.KITCHEN,
  Role.STAFF,
];
