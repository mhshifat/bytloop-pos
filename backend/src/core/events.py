"""Internal domain event bus.

Services emit events (``order.created``, ``product.updated``, …) and anyone
— including installed plugins — can subscribe. Stays in-process so the hot
path isn't blocked by Redis round-trips; real-time fan-out to other tabs
still goes through ``src.core.realtime`` as before.

Plugins register a handler via ``subscribe(event_name, handler)`` at app
boot. The handler receives a typed event dict and runs inside the same
request transaction — it can commit side effects, but a raised exception
will fail the originating request. Plugin handlers are expected to be fast
(sub-100ms) and idempotent; long work belongs on Celery.

Errors in a handler are caught per-handler so one bad plugin can't poison
an entire event fan-out. The failure is logged with the plugin code so the
operator can disable it from the UI.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger(__name__)

Handler = Callable[[dict[str, Any]], Awaitable[None]]
"""Async handler receiving the event payload (already JSON-serialisable)."""


class _EventBus:
    """Simple registry — module-level singleton; no per-request state."""

    def __init__(self) -> None:
        # Keyed by event name. One event name can have multiple subscribers;
        # order is registration order (plugins installed later run later).
        self._subscribers: dict[str, list[tuple[str, Handler]]] = defaultdict(list)

    def subscribe(self, event: str, handler: Handler, *, source: str) -> None:
        """Register ``handler`` for ``event``. ``source`` is the plugin code
        (or built-in module name) used in log lines so we can attribute
        failures without stringifying function objects.
        """
        self._subscribers[event].append((source, handler))

    def unsubscribe(self, event: str, source: str) -> None:
        """Remove all handlers registered by the given source."""
        self._subscribers[event] = [
            (s, h) for s, h in self._subscribers[event] if s != source
        ]

    def subscribers(self, event: str) -> list[tuple[str, Handler]]:
        return list(self._subscribers.get(event, ()))

    async def emit(self, event: str, payload: dict[str, Any]) -> None:
        """Fan out ``event`` with ``payload`` to every subscriber.

        Handlers run concurrently. Exceptions are isolated per-handler so
        one failing plugin can't break the emitter. Cross-plugin ordering
        is not guaranteed — don't rely on it.
        """
        handlers = self.subscribers(event)
        if not handlers:
            return
        results = await asyncio.gather(
            *(_safe_call(event, source, handler, payload) for source, handler in handlers),
            return_exceptions=False,
        )
        # Results are already logged in _safe_call; returning the list would
        # just leak internals to the caller.
        del results


async def _safe_call(
    event: str, source: str, handler: Handler, payload: dict[str, Any]
) -> None:
    try:
        await handler(payload)
    except Exception as exc:  # noqa: BLE001 — plugin sandbox
        logger.warning(
            "plugin_handler_failed",
            event=event,
            source=source,
            error=str(exc),
        )


bus = _EventBus()


# ──────────────────────────────────────────────
# Convenience helpers for emitters
# ──────────────────────────────────────────────


async def emit(event: str, payload: dict[str, Any]) -> None:
    """Module-level shortcut so services don't have to import the bus."""
    await bus.emit(event, payload)


def canonical_payload(
    *,
    tenant_id: UUID,
    actor_id: UUID | None,
    resource_id: str,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Standard envelope. Every event gets at least these fields so plugins
    can filter by tenant without string-munging per event."""
    payload: dict[str, Any] = {
        "tenantId": str(tenant_id),
        "actorId": str(actor_id) if actor_id else None,
        "resourceId": resource_id,
    }
    if extra:
        payload.update(extra)
    return payload
