"""bKash provider — sandbox-ready.

The real bKash flow is a multi-step "Create → Execute → Query" dance against
the Checkout (URL-based) or Tokenized Checkout API. We model it here as a
single ``charge`` call that accepts a ``provider_reference`` from the frontend
after the user completes the hosted flow. The provider token is fetched lazily
and cached for the token lifetime.
"""

from __future__ import annotations

import time

import httpx
import structlog

from src.integrations.payments.base import (
    PaymentIntent,
    PaymentOutcome,
    PaymentProvider,
    PaymentResult,
)

logger = structlog.get_logger(__name__)


class BKashPaymentProvider(PaymentProvider):
    provider_code = "bkash"

    def __init__(
        self,
        *,
        base_url: str,
        username: str,
        password: str,
        app_key: str,
        app_secret: str,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self._app_key = app_key
        self._app_secret = app_secret
        self._token: str | None = None
        self._token_expires_at: float = 0

    async def _get_token(self, client: httpx.AsyncClient) -> str:
        if self._token and time.time() < self._token_expires_at:
            return self._token
        response = await client.post(
            f"{self._base_url}/tokenized/checkout/token/grant",
            headers={
                "username": self._username,
                "password": self._password,
            },
            json={"app_key": self._app_key, "app_secret": self._app_secret},
        )
        response.raise_for_status()
        data = response.json()
        self._token = str(data["id_token"])
        self._token_expires_at = time.time() + int(data.get("expires_in", 3000))
        return self._token

    async def charge(self, intent: PaymentIntent) -> PaymentResult:
        if intent.customer_reference is None:
            return PaymentResult(
                outcome=PaymentOutcome.DECLINED,
                provider_reference="",
                raw_message="Missing bKash payment ID from client",
            )
        async with httpx.AsyncClient(timeout=10.0) as client:
            token = await self._get_token(client)
            response = await client.post(
                f"{self._base_url}/tokenized/checkout/execute",
                headers={
                    "authorization": token,
                    "x-app-key": self._app_key,
                },
                json={"paymentID": intent.customer_reference},
            )
        data = response.json() if response.content else {}
        status_code = data.get("statusCode", "")
        if response.status_code == 200 and status_code == "0000":
            return PaymentResult(
                outcome=PaymentOutcome.APPROVED,
                provider_reference=str(data.get("trxID", "")),
            )
        logger.warning("bkash_charge_declined", status=status_code)
        return PaymentResult(
            outcome=PaymentOutcome.DECLINED,
            provider_reference=str(data.get("paymentID", "")),
            raw_message=str(data.get("statusMessage", "")),
        )

    async def refund(
        self, *, provider_reference: str, amount_cents: int
    ) -> PaymentResult:
        # Full refund flow is via /refund endpoint — stubbed here.
        del provider_reference, amount_cents
        raise NotImplementedError("bKash refund — implement when partners confirm API")
