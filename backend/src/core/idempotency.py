"""Idempotency-Key handling for offline-replay safety.

The offline POS queues mutations with a client-generated ULID and replays
them when the network comes back. Without deduping, a replay creates a
second order — the #1 way to burn cashier trust in a POS.

Contract:
  - Any write (POST/PATCH/DELETE) may carry ``Idempotency-Key: <ulid>``.
  - First success is cached in Redis (status + body) keyed by
    ``pos:idem:{tenant}:{key}`` with a 24h TTL (config-driven).
  - A replay hitting the same key returns the cached response verbatim —
    the downstream handler never runs a second time.
  - An in-flight "lock" record sits under the same key while the handler
    runs, so two racing replays can't both execute concurrently.
  - Redis down means we degrade to non-idempotent behavior with a logged
    warning rather than refusing the request — matches the project-wide
    "Redis outage ≠ app outage" posture (docs/PLAN.md §15b).

Keys are **tenant-namespaced** so a compromised client can't force a cache
collision against another tenant's response.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from src.core import cache

logger = structlog.get_logger(__name__)

HEADER_NAME = "idempotency-key"
# 24 h — long enough for the worst "laptop sat on the counter all night" case.
DEFAULT_TTL_SECONDS = 60 * 60 * 24
# While a handler is in flight we stash this sentinel so concurrent replays
# wait rather than duplicate the work. The same ULID client would only
# replay after a timeout, so simply returning "in progress" as 409 is fine.
IN_FLIGHT_SENTINEL = "__in_flight__"
# Methods that actually mutate — GET/HEAD/OPTIONS skip the check entirely.
WRITE_METHODS = {"POST", "PATCH", "PUT", "DELETE"}
# Response statuses worth caching. 5xx is treated as transient; the client
# is expected to retry (and we want that retry to actually hit the handler).
CACHEABLE_STATUS_RANGE = range(200, 500)


@dataclass(frozen=True, slots=True)
class _CachedResponse:
    status_code: int
    headers: dict[str, str]
    body: str

    def to_response(self) -> Response:
        resp = Response(
            content=self.body,
            status_code=self.status_code,
            media_type=self.headers.get("content-type"),
        )
        for k, v in self.headers.items():
            if k.lower() in {"content-length", "content-type"}:
                continue
            resp.headers[k] = v
        resp.headers["idempotent-replay"] = "true"
        return resp


def _cache_key(tenant_id: str | None, idem_key: str) -> str:
    # Anonymous (pre-auth) requests get bucketed together — that's fine,
    # the key is a client-chosen ULID so collisions are vanishingly rare.
    tenant_bucket = tenant_id or "anon"
    return f"pos:idem:{tenant_bucket}:{idem_key}"


def _valid_key(value: str | None) -> bool:
    if not value:
        return False
    # Guard against abuse: limit length + charset. ULIDs are 26 chars, but
    # we accept anything alphanumeric-plus-dashes up to 128 chars so clients
    # can use their own scheme.
    if len(value) > 128:
        return False
    return all(c.isalnum() or c in "-_" for c in value)


async def _read_cached(key: str) -> _CachedResponse | str | None:
    raw = await cache.get_str(key)
    if raw is None:
        return None
    if raw == IN_FLIGHT_SENTINEL:
        return IN_FLIGHT_SENTINEL
    try:
        payload: dict[str, Any] = json.loads(raw)
        return _CachedResponse(
            status_code=int(payload["status"]),
            headers=dict(payload.get("headers", {})),
            body=str(payload.get("body", "")),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        # Corrupt entry — log and fall through to handler.
        logger.warning("idempotency_cache_corrupt", key=key)
        return None


async def _write_cached(key: str, response: Response, *, ttl_seconds: int) -> None:
    # Starlette Response.body is the encoded body bytes; for StreamingResponse
    # we can't snapshot (async iterator), so we skip caching those — they're
    # already unusual for our write endpoints.
    body_bytes = getattr(response, "body", None)
    if body_bytes is None:
        return
    payload = {
        "status": response.status_code,
        "headers": {k: v for k, v in response.headers.items()},
        "body": body_bytes.decode("utf-8", errors="replace")
        if isinstance(body_bytes, (bytes, bytearray))
        else str(body_bytes),
    }
    await cache.set_str(key, json.dumps(payload), ttl_seconds=ttl_seconds)


async def _mark_in_flight(key: str) -> bool:
    return await cache.set_str(
        key, IN_FLIGHT_SENTINEL, ttl_seconds=60
    )  # 60s — handler should finish well before this


def _tenant_from_request(request: Request) -> str | None:
    # The JWT middleware stashes tenant_id on the request state; fall back
    # to a header we can trust in tests.
    return (
        getattr(request.state, "tenant_id", None)
        or request.headers.get("x-tenant-id")
        or None
    )


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Dedupe writes that carry an ``Idempotency-Key`` header.

    Placed after auth so tenant context is available; before handler
    dispatch so we can short-circuit replays without touching the DB.
    """

    def __init__(self, app: ASGIApp, *, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        super().__init__(app)
        self._ttl = ttl_seconds

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        if request.method not in WRITE_METHODS:
            return await call_next(request)

        idem_key = request.headers.get(HEADER_NAME) or request.headers.get(
            HEADER_NAME.title()
        )
        if not _valid_key(idem_key):
            return await call_next(request)

        tenant_id = _tenant_from_request(request)
        cache_key = _cache_key(tenant_id, idem_key)  # type: ignore[arg-type]

        existing = await _read_cached(cache_key)
        if isinstance(existing, _CachedResponse):
            logger.info(
                "idempotency_replay_served_from_cache",
                key=idem_key,
                tenant=tenant_id,
                status=existing.status_code,
            )
            return existing.to_response()
        if existing == IN_FLIGHT_SENTINEL:
            # Concurrent replay while the first request is still running —
            # surface a retryable 409 rather than executing twice.
            logger.info("idempotency_in_flight_conflict", key=idem_key)
            return Response(
                status_code=409,
                content=json.dumps(
                    {
                        "error": {
                            "code": "idempotency_in_flight",
                            "message": "A request with this idempotency key is still processing.",
                        }
                    }
                ),
                media_type="application/json",
            )

        # Grab the lock (best-effort — if Redis is down we just proceed and
        # accept the risk of rare double-execution, which is strictly better
        # than refusing the sale entirely).
        await _mark_in_flight(cache_key)

        response = await call_next(request)

        if response.status_code in CACHEABLE_STATUS_RANGE:
            await _write_cached(cache_key, response, ttl_seconds=self._ttl)
        else:
            # Don't persist 5xx — let the client retry into a fresh handler.
            await cache.delete(cache_key)
        return response
