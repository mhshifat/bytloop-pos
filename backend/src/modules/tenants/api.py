"""Public interface for the tenants module.

Other modules MUST only import from this file (enforced by importlinter.ini).
"""

from src.modules.tenants.entity import Tenant, TenantHelpers
from src.modules.tenants.repository import TenantRepository

__all__ = ["Tenant", "TenantHelpers", "TenantRepository"]
