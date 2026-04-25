"""Cash — always approves, reference is a local ULID."""

from __future__ import annotations

from ulid import ULID

from src.integrations.payments.base import (
    PaymentIntent,
    PaymentOutcome,
    PaymentProvider,
    PaymentResult,
)


class CashPaymentProvider(PaymentProvider):
    provider_code = "cash"

    async def charge(self, intent: PaymentIntent) -> PaymentResult:
        return PaymentResult(
            outcome=PaymentOutcome.APPROVED,
            provider_reference=f"cash-{ULID()}",
        )

    async def refund(self, *, provider_reference: str, amount_cents: int) -> PaymentResult:
        del provider_reference, amount_cents
        return PaymentResult(
            outcome=PaymentOutcome.REFUNDED,
            provider_reference=f"cash-refund-{ULID()}",
        )
