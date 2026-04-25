"""Idempotency middleware — replay returns cached response, not double-exec."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from httpx import ASGITransport, AsyncClient

from src.core.idempotency import IdempotencyMiddleware


class _MemoryCache:
    """In-memory stand-in for ``src.core.cache`` used under test.

    Mirrors the three functions the middleware touches (``get_str``,
    ``set_str``, ``delete``). Keeps tests self-contained — no Redis required.
    """

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    async def get_str(self, key: str) -> str | None:
        return self._data.get(key)

    async def set_str(self, key: str, value: str, *, ttl_seconds: int) -> bool:
        self._data[key] = value
        return True

    async def delete(self, key: str) -> bool:
        self._data.pop(key, None)
        return True


@pytest.fixture
def memory_cache(monkeypatch):  # type: ignore[no-untyped-def]
    cache = _MemoryCache()
    # The middleware imports ``from src.core import cache`` and calls
    # ``cache.get_str`` / ``cache.set_str`` / ``cache.delete``.
    from src.core import idempotency

    monkeypatch.setattr(idempotency.cache, "get_str", cache.get_str)
    monkeypatch.setattr(idempotency.cache, "set_str", cache.set_str)
    monkeypatch.setattr(idempotency.cache, "delete", cache.delete)
    return cache


def _build_app(counter: dict[str, int]) -> FastAPI:
    app = FastAPI()
    app.add_middleware(IdempotencyMiddleware)

    @app.post("/orders")
    async def create_order(payload: dict[str, Any]) -> JSONResponse:
        counter["calls"] = counter.get("calls", 0) + 1
        return JSONResponse(
            {"id": f"order-{counter['calls']}", "amount": payload.get("amount", 0)},
            status_code=201,
        )

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        counter["reads"] = counter.get("reads", 0) + 1
        return {"ok": "yes"}

    return app


@pytest.mark.asyncio
async def test_same_key_replay_returns_cached_response(memory_cache):
    counter: dict[str, int] = {}
    app = _build_app(counter)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        first = await c.post(
            "/orders", json={"amount": 1000}, headers={"Idempotency-Key": "ulid-1"}
        )
        second = await c.post(
            "/orders", json={"amount": 1000}, headers={"Idempotency-Key": "ulid-1"}
        )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json() == second.json()
    # Handler only ran once even though two requests came in.
    assert counter["calls"] == 1
    # Replayed response is flagged so the client can distinguish.
    assert second.headers.get("idempotent-replay") == "true"


@pytest.mark.asyncio
async def test_different_keys_execute_independently(memory_cache):
    counter: dict[str, int] = {}
    app = _build_app(counter)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        a = await c.post("/orders", json={"amount": 1}, headers={"Idempotency-Key": "a"})
        b = await c.post("/orders", json={"amount": 2}, headers={"Idempotency-Key": "b"})

    assert a.status_code == 201
    assert b.status_code == 201
    assert a.json()["id"] != b.json()["id"]
    assert counter["calls"] == 2


@pytest.mark.asyncio
async def test_no_key_header_always_executes(memory_cache):
    counter: dict[str, int] = {}
    app = _build_app(counter)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        await c.post("/orders", json={"amount": 1})
        await c.post("/orders", json={"amount": 1})

    assert counter["calls"] == 2


@pytest.mark.asyncio
async def test_get_requests_skip_middleware(memory_cache):
    counter: dict[str, int] = {}
    app = _build_app(counter)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        for _ in range(3):
            await c.get("/ping", headers={"Idempotency-Key": "reused"})

    # Middleware must not cache reads — each GET hits the handler.
    assert counter["reads"] == 3


@pytest.mark.asyncio
async def test_malformed_key_is_ignored(memory_cache):
    counter: dict[str, int] = {}
    app = _build_app(counter)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        # Contains disallowed characters — treated as no key at all.
        await c.post(
            "/orders",
            json={"amount": 1},
            headers={"Idempotency-Key": "has spaces and $$$"},
        )
        await c.post(
            "/orders",
            json={"amount": 1},
            headers={"Idempotency-Key": "has spaces and $$$"},
        )

    assert counter["calls"] == 2


@pytest.mark.asyncio
async def test_server_error_is_not_cached_so_retry_can_succeed(memory_cache):
    """5xx responses must not be cached — the whole point of a retry is to
    hit a hopefully-fixed handler."""
    counter: dict[str, int] = {}
    app = FastAPI()
    app.add_middleware(IdempotencyMiddleware)

    @app.post("/flaky")
    async def flaky() -> JSONResponse:
        counter["calls"] = counter.get("calls", 0) + 1
        if counter["calls"] == 1:
            return JSONResponse({"error": "boom"}, status_code=500)
        return JSONResponse({"ok": True}, status_code=201)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        first = await c.post("/flaky", headers={"Idempotency-Key": "retry-me"})
        second = await c.post("/flaky", headers={"Idempotency-Key": "retry-me"})

    assert first.status_code == 500
    assert second.status_code == 201
    assert counter["calls"] == 2


@pytest.mark.asyncio
async def test_client_error_is_cached_so_poison_doesnt_loop(memory_cache):
    """Well-formed 4xx (e.g. validation) IS cached — replaying it would get
    the same answer anyway, and caching stops the queue hammering on it."""
    counter: dict[str, int] = {}
    app = FastAPI()
    app.add_middleware(IdempotencyMiddleware)

    @app.post("/reject")
    async def reject() -> JSONResponse:
        counter["calls"] = counter.get("calls", 0) + 1
        return JSONResponse({"error": "bad"}, status_code=400)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        await c.post("/reject", headers={"Idempotency-Key": "poison"})
        await c.post("/reject", headers={"Idempotency-Key": "poison"})

    assert counter["calls"] == 1
