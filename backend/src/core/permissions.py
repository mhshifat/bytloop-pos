"""Role and permission catalog — single source of truth.

Shape mirrored to the frontend via a generated `lib/rbac.ts` (see scripts/).
Placeholder data for now; will be populated as modules add their permissions.
"""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    OWNER = "owner"
    MANAGER = "manager"
    CASHIER = "cashier"
    KITCHEN = "kitchen"
    STAFF = "staff"


class Permission(StrEnum):
    # Admin / platform
    ADMIN_ACCESS = "admin.access"
    SETTINGS_MANAGE = "settings.manage"
    STAFF_MANAGE = "staff.manage"
    AUDIT_VIEW = "audit.view"

    # Catalog
    PRODUCTS_READ = "products.read"
    PRODUCTS_WRITE = "products.write"

    # Sales
    ORDERS_CREATE = "orders.create"
    ORDERS_REFUND = "orders.refund"
    ORDERS_VOID = "orders.void"

    # Reports
    REPORTS_VIEW = "reports.view"


ROLE_PERMISSIONS: dict[Role, frozenset[Permission]] = {
    Role.OWNER: frozenset(Permission),  # owner gets everything
    Role.MANAGER: frozenset(
        {
            Permission.ADMIN_ACCESS,
            Permission.STAFF_MANAGE,
            Permission.PRODUCTS_READ,
            Permission.PRODUCTS_WRITE,
            Permission.ORDERS_CREATE,
            Permission.ORDERS_REFUND,
            Permission.ORDERS_VOID,
            Permission.REPORTS_VIEW,
            Permission.AUDIT_VIEW,
        }
    ),
    Role.CASHIER: frozenset(
        {
            Permission.PRODUCTS_READ,
            Permission.ORDERS_CREATE,
        }
    ),
    Role.KITCHEN: frozenset({Permission.ORDERS_CREATE}),
    Role.STAFF: frozenset({Permission.PRODUCTS_READ}),
}


def permissions_for(roles: list[Role]) -> set[Permission]:
    out: set[Permission] = set()
    for role in roles:
        out.update(ROLE_PERMISSIONS.get(role, frozenset()))
    return out
