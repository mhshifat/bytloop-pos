"""Error hierarchy + global FastAPI exception handlers.

Every error — expected or unexpected — produces a correlation ID on the server log
(with full stacktrace and context) while the client sees ONLY::

    {"error": {"correlation_id", "code", "message", "details"}}

Anything outside that shape is stripped. See docs/PLAN.md §12.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from src.core.correlation import get_correlation_id

logger = structlog.get_logger(__name__)


# ──────────────────────────────────────────────
# Exception hierarchy
# ──────────────────────────────────────────────


class AppError(Exception):
    """Base application error.

    Subclass per domain case. ``user_message`` is the ONLY text allowed to reach
    the client. ``code`` is a stable machine-readable key (snake_case).
    """

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    code: str = "internal_error"
    user_message: str = "Something went wrong. Please try again."

    def __init__(
        self,
        user_message: str | None = None,
        *,
        code: str | None = None,
        details: Any = None,
        log_extras: dict[str, Any] | None = None,
    ) -> None:
        self.user_message = user_message or self.user_message
        self.code = code or self.code
        self.details = details
        self.log_extras = log_extras or {}
        super().__init__(self.user_message)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    code = "not_found"
    user_message = "We couldn't find what you're looking for."


class ValidationError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    code = "validation_failed"
    user_message = "Please check the highlighted fields."


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "unauthorized"
    user_message = "Please sign in to continue."


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "forbidden"
    user_message = "You don't have permission to do that."


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    code = "conflict"
    user_message = "That action conflicts with the current state."


class RateLimitError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    code = "rate_limited"
    user_message = "You're doing that too often. Please wait a moment."


# ──────────────────────────────────────────────
# Response shape — whitelist only
# ──────────────────────────────────────────────


def _build_error_body(
    *,
    correlation_id: str,
    code: str,
    message: str,
    details: Any = None,
) -> dict[str, Any]:
    """Return the ONLY shape that ever leaves the server."""
    return {
        "error": {
            "correlationId": correlation_id,
            "code": code,
            "message": message,
            "details": details,
        }
    }


def _sanitize_validation_errors(errors: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    """Strip Pydantic internals; keep only top-level field name + human message."""
    sanitized: list[dict[str, str]] = []
    seen: set[str] = set()
    for err in errors:
        loc = err.get("loc", ())
        # loc is like ("body", "email") — we want the last non-internal segment
        field = next(
            (str(p) for p in reversed(loc) if p not in ("body", "query", "path", "header")),
            "field",
        )
        if field in seen:
            continue
        seen.add(field)
        sanitized.append({"field": field, "message": err.get("msg", "Invalid value")})
    return sanitized


# ──────────────────────────────────────────────
# Handlers
# ──────────────────────────────────────────────


async def _handle_app_error(request: Request, exc: AppError) -> JSONResponse:
    correlation_id = get_correlation_id()
    logger.warning(
        "app_error",
        code=exc.code,
        status_code=exc.status_code,
        message=exc.user_message,
        path=request.url.path,
        method=request.method,
        **exc.log_extras,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=_build_error_body(
            correlation_id=correlation_id,
            code=exc.code,
            message=exc.user_message,
            details=exc.details,
        ),
        headers={"X-Correlation-Id": correlation_id},
    )


async def _handle_validation_error(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    correlation_id = get_correlation_id()
    sanitized = _sanitize_validation_errors(exc.errors())
    logger.info(
        "validation_error",
        path=request.url.path,
        method=request.method,
        field_count=len(sanitized),
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=_build_error_body(
            correlation_id=correlation_id,
            code="validation_failed",
            message="Please check the highlighted fields.",
            details=sanitized,
        ),
        headers={"X-Correlation-Id": correlation_id},
    )


async def _handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    correlation_id = get_correlation_id()
    logger.exception(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        exception_type=type(exc).__name__,
    )
    # Never leak the exception message or type to the client.
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=_build_error_body(
            correlation_id=correlation_id,
            code="internal_error",
            message="Something went wrong. Please try again.",
            details=None,
        ),
        headers={"X-Correlation-Id": correlation_id},
    )


def register_error_handlers(app: FastAPI) -> None:
    """Wire all handlers onto the FastAPI app."""
    app.add_exception_handler(AppError, _handle_app_error)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _handle_validation_error)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _handle_unexpected)
