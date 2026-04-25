"""Built-in plugins.

A plugin is a metadata record + a ``register`` callable that subscribes
handlers to the event bus on app startup. We deliberately keep this small
and in-tree for MVP — a package-discovery mechanism (``importlib.metadata``
entry points) can slot in later without disturbing the tenant-install model.

Each built-in:
  - declares a unique ``code`` used as the tenant install key
  - declares the event names it listens to (so the UI can show it)
  - provides a ``register`` that wires actual handlers to ``core.events``

Handlers are registered once per-tenant at enable time, so there's no cross
-tenant leak: the handler closes over the tenant_id it was enabled for.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import structlog

from src.core.events import bus

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class PluginMeta:
    code: str
    name: str
    description: str
    version: str
    hooks: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Plugin:
    meta: PluginMeta
    """Wire handlers for a specific tenant. Return a teardown callable so the
    registry can unsubscribe cleanly on uninstall."""
    register: "Callable[[UUID, dict[str, Any]], None]"  # type: ignore[name-defined]
    unregister: "Callable[[UUID], None]"  # type: ignore[name-defined]


# ──────────────────────────────────────────────
# Built-in: low-stock alerter
# ──────────────────────────────────────────────


def _low_stock_plugin() -> Plugin:
    meta = PluginMeta(
        code="low-stock-logger",
        name="Low-stock logger",
        description=(
            "When an order drops an inventory level at or below its reorder "
            "point, write a structured log line. Drop-in replacement for a "
            "Slack/SMS plugin — just swap the handler body."
        ),
        version="1.0.0",
        hooks=("order.completed",),
    )
    source_key = "plugin:low-stock-logger"

    def _make_handler(tenant_id: UUID):  # type: ignore[no-untyped-def]
        async def handler(payload: dict[str, Any]) -> None:
            if payload.get("tenantId") != str(tenant_id):
                return
            low = payload.get("lowStock") or []
            if not low:
                return
            logger.info(
                "plugin_low_stock_alert",
                tenant_id=str(tenant_id),
                order_id=payload.get("resourceId"),
                products=low,
            )

        return handler

    def register(tenant_id: UUID, _config: dict[str, Any]) -> None:
        bus.subscribe(
            "order.completed",
            _make_handler(tenant_id),
            source=f"{source_key}:{tenant_id}",
        )

    def unregister(tenant_id: UUID) -> None:
        bus.unsubscribe("order.completed", source=f"{source_key}:{tenant_id}")

    return Plugin(meta=meta, register=register, unregister=unregister)


# ──────────────────────────────────────────────
# Built-in: new-customer welcomer
# ──────────────────────────────────────────────


def _welcome_plugin() -> Plugin:
    meta = PluginMeta(
        code="welcome-new-customer",
        name="Welcome new customer",
        description=(
            "Log a welcome message when a customer is created. Wire this up "
            "to your email adapter to send a real welcome email."
        ),
        version="1.0.0",
        hooks=("customer.created",),
    )
    source_key = "plugin:welcome-new-customer"

    def _make_handler(tenant_id: UUID):  # type: ignore[no-untyped-def]
        async def handler(payload: dict[str, Any]) -> None:
            if payload.get("tenantId") != str(tenant_id):
                return
            logger.info(
                "plugin_welcome_customer",
                tenant_id=str(tenant_id),
                customer_id=payload.get("resourceId"),
                email=payload.get("email"),
            )

        return handler

    def register(tenant_id: UUID, _config: dict[str, Any]) -> None:
        bus.subscribe(
            "customer.created",
            _make_handler(tenant_id),
            source=f"{source_key}:{tenant_id}",
        )

    def unregister(tenant_id: UUID) -> None:
        bus.unsubscribe("customer.created", source=f"{source_key}:{tenant_id}")

    return Plugin(meta=meta, register=register, unregister=unregister)


# Module-level catalog. Adding a plugin = append a factory here.
_ALL: dict[str, Plugin] = {
    "low-stock-logger": _low_stock_plugin(),
    "welcome-new-customer": _welcome_plugin(),
}


def available_plugins() -> list[PluginMeta]:
    return [p.meta for p in _ALL.values()]


def get_plugin(code: str) -> Plugin | None:
    return _ALL.get(code)
