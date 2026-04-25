"""Redis wrapper with timeouts + circuit breaker.

Free-tier Redis (20 MB / 30 conn) must never block the app. Every call here
has a hard op timeout; consecutive failures trip the breaker so subsequent
calls fail fast until the cooldown elapses. See docs/PLAN.md §15b.
"""

from __future__ import annotations

import asyncio
import time
from typing import Literal

import redis.asyncio as redis
import structlog

from src.core.config import settings

logger = structlog.get_logger(__name__)


class _CircuitBreaker:
    """Minimal breaker — no external deps, safe for async."""

    __slots__ = ("_failures", "_opened_at", "_state")

    def __init__(self) -> None:
        self._failures = 0
        self._opened_at: float | None = None
        self._state: Literal["closed", "open", "half_open"] = "closed"

    @property
    def state(self) -> str:
        return self._state

    def allow(self) -> bool:
        if self._state == "closed":
            return True
        if self._state == "open":
            assert self._opened_at is not None
            if time.monotonic() - self._opened_at >= settings.redis.circuit_breaker_cooldown_seconds:
                self._state = "half_open"
                return True
            return False
        # half_open
        return True

    def record_success(self) -> None:
        self._failures = 0
        self._opened_at = None
        self._state = "closed"

    def record_failure(self) -> None:
        self._failures += 1
        if self._failures >= settings.redis.circuit_breaker_threshold:
            self._state = "open"
            self._opened_at = time.monotonic()


_pool: redis.ConnectionPool | None = None
_breaker = _CircuitBreaker()


def _pool_instance() -> redis.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool.from_url(
            settings.redis.url,
            db=settings.redis.db,
            max_connections=settings.redis.max_app_connections,
            socket_timeout=settings.redis.socket_timeout_seconds,
            socket_connect_timeout=settings.redis.socket_connect_timeout_seconds,
        )
    return _pool


def _client() -> redis.Redis:
    return redis.Redis(connection_pool=_pool_instance())


async def dispose_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.disconnect(inuse_connections=True)
        _pool = None


# ──────────────────────────────────────────────
# Public API — safe, non-blocking
# ──────────────────────────────────────────────


async def get_str(key: str) -> str | None:
    if not _breaker.allow():
        return None
    try:
        raw = await asyncio.wait_for(_client().get(key), settings.redis.op_timeout_seconds)
    except (TimeoutError, asyncio.TimeoutError, redis.RedisError):
        _breaker.record_failure()
        logger.warning("redis_get_failed", key=key)
        return None
    _breaker.record_success()
    return raw.decode("utf-8") if isinstance(raw, bytes) else raw


async def set_str(key: str, value: str, *, ttl_seconds: int) -> bool:
    if not _breaker.allow():
        return False
    try:
        await asyncio.wait_for(
            _client().set(key, value, ex=ttl_seconds), settings.redis.op_timeout_seconds
        )
    except (TimeoutError, asyncio.TimeoutError, redis.RedisError):
        _breaker.record_failure()
        logger.warning("redis_set_failed", key=key)
        return False
    _breaker.record_success()
    return True


async def delete(key: str) -> bool:
    if not _breaker.allow():
        return False
    try:
        await asyncio.wait_for(_client().delete(key), settings.redis.op_timeout_seconds)
    except (TimeoutError, asyncio.TimeoutError, redis.RedisError):
        _breaker.record_failure()
        return False
    _breaker.record_success()
    return True


async def ttl(key: str) -> int | None:
    """Returns remaining TTL in seconds, or ``None`` on failure."""
    if not _breaker.allow():
        return None
    try:
        value = await asyncio.wait_for(_client().ttl(key), settings.redis.op_timeout_seconds)
    except (TimeoutError, asyncio.TimeoutError, redis.RedisError):
        _breaker.record_failure()
        return None
    _breaker.record_success()
    if value is None or value < 0:
        return None
    return int(value)


def breaker_state() -> str:
    return _breaker.state
