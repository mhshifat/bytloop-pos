"""Payment webhook signature verification — fails closed on bad sigs."""

from __future__ import annotations

import hashlib
import hmac
import json
import os

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.core.correlation import CorrelationIdMiddleware
from src.core.errors import register_error_handlers
from src.integrations.payments.webhooks import router as webhooks_router


def _build_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(CorrelationIdMiddleware)
    register_error_handlers(app)
    app.include_router(webhooks_router)
    return app


@pytest.mark.asyncio
async def test_stripe_webhook_without_signature_rejected(monkeypatch):
    monkeypatch.setenv("PAYMENTS_STRIPE_WEBHOOK_SECRET", "whsec_test")
    app = _build_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/payments/webhooks/stripe", content=b"{}")
    assert resp.status_code == 401
    body = resp.json()
    assert body["error"]["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_stripe_webhook_with_bad_signature_rejected(monkeypatch):
    monkeypatch.setenv("PAYMENTS_STRIPE_WEBHOOK_SECRET", "whsec_test")
    app = _build_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/payments/webhooks/stripe",
            content=b"{}",
            headers={"Stripe-Signature": "t=1,v1=deadbeef"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_stripe_webhook_with_valid_signature_accepted(monkeypatch, db_session):
    # db_session is injected by conftest even though our app uses its own get_db
    secret = "whsec_test"
    monkeypatch.setenv("PAYMENTS_STRIPE_WEBHOOK_SECRET", secret)

    payload = json.dumps({"type": "ping"}).encode("utf-8")
    timestamp = "1700000000"
    signed = f"{timestamp}.{payload.decode('utf-8')}".encode()
    sig = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()

    app = _build_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/payments/webhooks/stripe",
            content=payload,
            headers={"Stripe-Signature": f"t={timestamp},v1={sig}"},
        )
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_bkash_webhook_signature_mismatch(monkeypatch):
    monkeypatch.setenv("PAYMENTS_BKASH_WEBHOOK_SECRET", "bkash_test")
    app = _build_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/payments/webhooks/bkash",
            content=b'{"trxID":"X"}',
            headers={"X-BKASH-SIGNATURE": "wrong"},
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_bkash_webhook_valid_signature_accepted(monkeypatch):
    secret = "bkash_test"
    monkeypatch.setenv("PAYMENTS_BKASH_WEBHOOK_SECRET", secret)
    payload = b'{"trxID":"X","status":"Completed","amount":"1.00"}'
    sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    app = _build_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post(
            "/payments/webhooks/bkash",
            content=payload,
            headers={"X-BKASH-SIGNATURE": sig},
        )
    assert resp.status_code == 200
