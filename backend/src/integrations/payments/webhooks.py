"""Payment provider webhooks.

Providers send async notifications for payment state changes (authorization,
capture, refund). We verify signatures, dedupe by provider id, and dispatch to
the relevant service to update order/payment records.

Stripe webhook verification uses the `Stripe-Signature` header + timestamp +
secret. bKash (tokenized checkout) signs with the app secret over the JSON body.

For the MVP this endpoint logs and acknowledges — the subsequent increment
wires the update back into ``SalesService.mark_payment_settled`` once the
mutation API is in place.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os

import structlog
from fastapi import APIRouter, Header, Request, status
from fastapi.responses import Response
from sqlalchemy import select

from src.core.deps import DbSession
from src.core.errors import UnauthorizedError
from src.modules.sales.entity import Order, OrderStatus, Payment

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/payments/webhooks", tags=["payments"])


def _verify_stripe(payload: bytes, header: str | None) -> None:
    secret = os.environ.get("PAYMENTS_STRIPE_WEBHOOK_SECRET", "")
    if not secret or not header:
        raise UnauthorizedError("Webhook signature missing or secret not configured.")
    # Stripe sends "t=<timestamp>,v1=<signature>,v1=<signature>..."
    parts = dict(p.split("=", 1) for p in header.split(",") if "=" in p)
    timestamp = parts.get("t")
    signature = parts.get("v1")
    if timestamp is None or signature is None:
        raise UnauthorizedError("Malformed Stripe-Signature header.")
    signed = f"{timestamp}.{payload.decode('utf-8')}".encode()
    expected = hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise UnauthorizedError("Invalid Stripe webhook signature.")


def _verify_bkash(payload: bytes, header: str | None) -> None:
    secret = os.environ.get("PAYMENTS_BKASH_WEBHOOK_SECRET", "")
    if not secret or not header:
        raise UnauthorizedError("Webhook signature missing or secret not configured.")
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, header.strip()):
        raise UnauthorizedError("Invalid bKash webhook signature.")


async def _mark_payment_settled(
    db: DbSession,
    *,
    provider_reference: str,
    amount_cents: int | None,
) -> None:
    """Lookup the payment by provider reference and bump its order to completed
    if it's still open. Idempotent by design — multiple webhook deliveries
    converge on the same terminal state.
    """
    if not provider_reference:
        return
    stmt = select(Payment).where(Payment.reference == provider_reference)
    payment = (await db.execute(stmt)).scalar_one_or_none()
    if payment is None:
        logger.info("webhook_payment_not_found", reference=provider_reference)
        return
    if amount_cents is not None and payment.amount_cents != amount_cents:
        logger.warning(
            "webhook_amount_mismatch",
            reference=provider_reference,
            expected=payment.amount_cents,
            received=amount_cents,
        )

    order = await db.get(Order, payment.order_id)
    if order is None:
        return
    if order.status == OrderStatus.OPEN:
        order.status = OrderStatus.COMPLETED
        await db.flush()


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    db: DbSession,
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
) -> Response:
    payload = await request.body()
    _verify_stripe(payload, stripe_signature)

    try:
        event = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.warning("stripe_webhook_malformed_payload")
        return Response(status_code=status.HTTP_200_OK)

    event_type = event.get("type", "")
    data_object = event.get("data", {}).get("object", {}) or {}
    intent_id = data_object.get("id")
    amount = data_object.get("amount")

    logger.info(
        "stripe_webhook_received",
        event_type=event_type,
        intent_id=intent_id,
    )

    if event_type == "payment_intent.succeeded" and isinstance(intent_id, str):
        await _mark_payment_settled(
            db,
            provider_reference=intent_id,
            amount_cents=amount if isinstance(amount, int) else None,
        )
    return Response(status_code=status.HTTP_200_OK)


@router.post("/bkash", status_code=status.HTTP_200_OK)
async def bkash_webhook(
    request: Request,
    db: DbSession,
    signature: str | None = Header(default=None, alias="X-BKASH-SIGNATURE"),
) -> Response:
    payload = await request.body()
    _verify_bkash(payload, signature)

    try:
        event = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        logger.warning("bkash_webhook_malformed_payload")
        return Response(status_code=status.HTTP_200_OK)

    trx_id = event.get("trxID") or event.get("trxId")
    amount_raw = event.get("amount")
    # bKash amounts come as strings (e.g. "100.00"); normalize to cents.
    amount_cents: int | None = None
    if isinstance(amount_raw, str):
        try:
            amount_cents = int(round(float(amount_raw) * 100))
        except ValueError:
            amount_cents = None

    logger.info("bkash_webhook_received", trx_id=trx_id)

    if isinstance(trx_id, str) and event.get("status") in ("Completed", "SUCCESS", "0000"):
        await _mark_payment_settled(
            db,
            provider_reference=trx_id,
            amount_cents=amount_cents,
        )
    return Response(status_code=status.HTTP_200_OK)
