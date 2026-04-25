"""Payment provider abstraction — Strategy pattern."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum


class PaymentOutcome(StrEnum):
    APPROVED = "approved"
    PENDING = "pending"
    DECLINED = "declined"
    REFUNDED = "refunded"


@dataclass(frozen=True, slots=True)
class PaymentIntent:
    order_id: str
    amount_cents: int
    currency: str
    customer_reference: str | None = None
    idempotency_key: str | None = None


@dataclass(frozen=True, slots=True)
class PaymentResult:
    outcome: PaymentOutcome
    provider_reference: str
    raw_message: str | None = None


class PaymentProvider(ABC):
    """Every provider (bKash, Nagad, Stripe, ...) implements this."""

    provider_code: str

    @abstractmethod
    async def charge(self, intent: PaymentIntent) -> PaymentResult: ...

    @abstractmethod
    async def refund(
        self, *, provider_reference: str, amount_cents: int
    ) -> PaymentResult: ...
