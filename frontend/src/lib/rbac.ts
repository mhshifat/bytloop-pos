/**
 * Role / permission catalog — mirrored from backend `core/permissions.py`.
 *
 * Kept in sync by code-gen (TBD); for now, update both sides together.
 * See docs/PLAN.md §11 RBAC.
 */

export const Role = {
  OWNER: "owner",
  MANAGER: "manager",
  CASHIER: "cashier",
  KITCHEN: "kitchen",
  STAFF: "staff",
} as const;

export type Role = (typeof Role)[keyof typeof Role];

export const Permission = {
  ADMIN_ACCESS: "admin.access",
  SETTINGS_MANAGE: "settings.manage",
  STAFF_MANAGE: "staff.manage",
  AUDIT_VIEW: "audit.view",

  PRODUCTS_READ: "products.read",
  PRODUCTS_WRITE: "products.write",

  ORDERS_CREATE: "orders.create",
  ORDERS_REFUND: "orders.refund",
  ORDERS_VOID: "orders.void",

  REPORTS_VIEW: "reports.view",
} as const;

export type Permission = (typeof Permission)[keyof typeof Permission];

const ROLE_PERMISSIONS: Record<Role, ReadonlySet<Permission>> = {
  [Role.OWNER]: new Set(Object.values(Permission)),
  [Role.MANAGER]: new Set<Permission>([
    Permission.ADMIN_ACCESS,
    Permission.STAFF_MANAGE,
    Permission.PRODUCTS_READ,
    Permission.PRODUCTS_WRITE,
    Permission.ORDERS_CREATE,
    Permission.ORDERS_REFUND,
    Permission.ORDERS_VOID,
    Permission.REPORTS_VIEW,
    Permission.AUDIT_VIEW,
  ]),
  [Role.CASHIER]: new Set<Permission>([Permission.PRODUCTS_READ, Permission.ORDERS_CREATE]),
  [Role.KITCHEN]: new Set<Permission>([Permission.ORDERS_CREATE]),
  [Role.STAFF]: new Set<Permission>([Permission.PRODUCTS_READ]),
};

export function permissionsForRoles(roles: readonly Role[]): ReadonlySet<Permission> {
  const out = new Set<Permission>();
  for (const role of roles) {
    const perms = ROLE_PERMISSIONS[role];
    if (perms) for (const p of perms) out.add(p);
  }
  return out;
}

export function hasPermission(
  userRoles: readonly Role[],
  required: Permission
): boolean {
  return permissionsForRoles(userRoles).has(required);
}
