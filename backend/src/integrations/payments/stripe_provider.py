"""Stripe provider — uses PaymentIntents.

The intent id is created on the client (via Elements) and passed as
``customer_reference``. We confirm via the Stripe API here for server-side
authoritative state.
"""

from __future__ import annotations

import httpx
import structlog

from src.integrations.payments.base import (
    PaymentIntent,
    PaymentOutcome,
    PaymentProvider,
    PaymentResult,
)

logger = structlog.get_logger(__name__)


class StripePaymentProvider(PaymentProvider):
    provider_code = "stripe"

    def __init__(self, *, api_key: str) -> None:
        self._api_key = api_key

    async def charge(self, intent: PaymentIntent) -> PaymentResult:
        if intent.customer_reference is None:
            return PaymentResult(
                outcome=PaymentOutcome.DECLINED,
                provider_reference="",
                raw_message="Missing Stripe PaymentIntent id",
            )
        async with httpx.AsyncClient(timeout=10.0, auth=(self._api_key, "")) as client:
            response = await client.post(
                f"https://api.stripe.com/v1/payment_intents/{intent.customer_reference}/confirm",
                headers={
                    "Idempotency-Key": intent.idempotency_key or intent.order_id,
                },
            )
        data = response.json() if response.content else {}
        status = data.get("status")
        if status == "succeeded":
            return PaymentResult(
                outcome=PaymentOutcome.APPROVED,
                provider_reference=str(data.get("id", "")),
            )
        if status in {"processing", "requires_action"}:
            return PaymentResult(
                outcome=PaymentOutcome.PENDING,
                provider_reference=str(data.get("id", "")),
                raw_message=status,
            )
        logger.warning("stripe_charge_declined", status=status)
        return PaymentResult(
            outcome=PaymentOutcome.DECLINED,
            provider_reference=str(data.get("id", "")),
            raw_message=str(status),
        )

    async def refund(
        self, *, provider_reference: str, amount_cents: int
    ) -> PaymentResult:
        async with httpx.AsyncClient(timeout=10.0, auth=(self._api_key, "")) as client:
            response = await client.post(
                "https://api.stripe.com/v1/refunds",
                data={
                    "payment_intent": provider_reference,
                    "amount": str(amount_cents),
                },
            )
        data = response.json() if response.content else {}
        return PaymentResult(
            outcome=PaymentOutcome.REFUNDED if data.get("status") == "succeeded" else PaymentOutcome.DECLINED,
            provider_reference=str(data.get("id", "")),
            raw_message=str(data.get("status")),
        )
