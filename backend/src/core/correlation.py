"""Correlation-ID middleware + contextvar.

Every request gets a ULID correlation ID (or the caller's ``X-Correlation-Id``).
The ID is stored in a ``contextvars.ContextVar`` so every log line picks it up
automatically via ``structlog``'s context-local processor.
"""

from __future__ import annotations

from contextvars import ContextVar

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from ulid import ULID

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")

CORRELATION_HEADER = "X-Correlation-Id"


def get_correlation_id() -> str:
    """Return the current request's correlation ID, or generate a fresh one."""
    cid = _correlation_id.get()
    if not cid:
        cid = str(ULID())
        _correlation_id.set(cid)
    return cid


def set_correlation_id(cid: str) -> None:
    _correlation_id.set(cid)


def bind_correlation_to_structlog() -> structlog.stdlib.BoundLogger:
    """Helper for task contexts where middleware isn't in play."""
    return structlog.get_logger().bind(correlation_id=get_correlation_id())


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Read or mint a correlation ID, store it, echo it on the response."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        incoming = request.headers.get(CORRELATION_HEADER)
        cid = incoming if incoming else str(ULID())
        token = _correlation_id.set(cid)
        try:
            response: Response = await call_next(request)
        finally:
            _correlation_id.reset(token)
        response.headers[CORRELATION_HEADER] = cid
        return response
