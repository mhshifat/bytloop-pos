"""Verify no internals leak through the error response body.

This is the non-exposure fuzz test from docs/PLAN.md §12.
"""

from __future__ import annotations

import json

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from src.core.correlation import CorrelationIdMiddleware
from src.core.errors import AppError, NotFoundError, register_error_handlers

FORBIDDEN_SUBSTRINGS = (
    "Traceback",
    "sqlalchemy",
    "asyncpg",
    "pydantic_core",
    "File \"",
    "at 0x",
    "/app/",
    "/usr/",
    "NoneType",
    "KeyError",
    "AttributeError",
)


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    register_error_handlers(app)

    @app.get("/ok")
    async def ok() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/notfound")
    async def notfound() -> None:
        raise NotFoundError("We couldn't find that widget.")

    @app.get("/boom")
    async def boom() -> None:
        _ = {}["missing"]

    @app.get("/app-error")
    async def app_error() -> None:
        raise AppError("Upstream hiccup.", code="upstream_error")

    return app


@pytest.mark.asyncio
async def test_unhandled_exception_never_leaks_internals():
    app = _build_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/boom")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    body_text = response.text
    for substring in FORBIDDEN_SUBSTRINGS:
        assert substring not in body_text, f"Leaked internal: {substring!r}"

    envelope = response.json()
    assert set(envelope.keys()) == {"error"}
    assert set(envelope["error"].keys()) == {"correlationId", "code", "message", "details"}
    assert envelope["error"]["code"] == "internal_error"
    assert response.headers["X-Correlation-Id"] == envelope["error"]["correlationId"]


@pytest.mark.asyncio
async def test_app_error_emits_whitelisted_envelope_only():
    app = _build_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/notfound")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    envelope = response.json()
    assert envelope["error"]["code"] == "not_found"
    assert envelope["error"]["message"] == "We couldn't find that widget."


@pytest.mark.asyncio
async def test_correlation_id_propagates_from_request_header():
    app = _build_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ok", headers={"X-Correlation-Id": "caller-supplied"})
    assert response.headers["X-Correlation-Id"] == "caller-supplied"


@pytest.mark.asyncio
async def test_validation_errors_are_sanitized():
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    register_error_handlers(app)

    from pydantic import BaseModel

    class In(BaseModel):
        age: int

    @app.post("/validate")
    async def validate(_: In) -> dict[str, str]:
        return {"ok": "ok"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/validate", content=json.dumps({"age": "not-an-int"}))

    envelope = response.json()
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert envelope["error"]["code"] == "validation_failed"
    assert isinstance(envelope["error"]["details"], list)
    assert "age" == envelope["error"]["details"][0]["field"]
    # No leakage of Pydantic internals
    assert "ctx" not in response.text
    assert "type_error" not in response.text
