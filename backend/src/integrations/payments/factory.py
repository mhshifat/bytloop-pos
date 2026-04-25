"""Payment provider factory — returns the Strategy by code."""

from __future__ import annotations

import os
from functools import lru_cache

from src.core.errors import AppError
from src.integrations.payments.base import PaymentProvider
from src.integrations.payments.bkash_provider import BKashPaymentProvider
from src.integrations.payments.cash_provider import CashPaymentProvider
from src.integrations.payments.stripe_provider import StripePaymentProvider


@lru_cache(maxsize=8)
def get_payment_provider(code: str) -> PaymentProvider:
    if code == "cash":
        return CashPaymentProvider()
    if code == "bkash":
        return BKashPaymentProvider(
            base_url=os.environ.get("PAYMENTS_BKASH_BASE_URL", "https://tokenized.sandbox.bka.sh/v1.2.0-beta"),
            username=os.environ.get("PAYMENTS_BKASH_USERNAME", ""),
            password=os.environ.get("PAYMENTS_BKASH_PASSWORD", ""),
            app_key=os.environ.get("PAYMENTS_BKASH_APP_KEY", ""),
            app_secret=os.environ.get("PAYMENTS_BKASH_APP_SECRET", ""),
        )
    if code == "stripe":
        api_key = os.environ.get("PAYMENTS_STRIPE_API_KEY", "")
        if not api_key:
            raise AppError(
                "Stripe isn't configured for this workspace.",
                code="payment_provider_not_configured",
            )
        return StripePaymentProvider(api_key=api_key)
    raise AppError(
        f"Payment method '{code}' isn't available.",
        code="payment_method_unsupported",
    )
