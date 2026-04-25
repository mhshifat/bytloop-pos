"""Mailgun adapter — production primary."""

from __future__ import annotations

import httpx
import structlog

from src.core.config import settings
from src.integrations.email.base import EmailAdapter, EmailMessage

logger = structlog.get_logger(__name__)


class MailgunEmailAdapter(EmailAdapter):
    """Sends via Mailgun's HTTP API. Fast, idempotent with 'v:correlation-id'."""

    async def send(self, message: EmailMessage) -> None:
        cfg = settings.email
        api_key = cfg.mailgun_api_key.get_secret_value()
        if not api_key or not cfg.mailgun_domain:
            raise RuntimeError("Mailgun adapter selected but credentials are empty")

        url = f"https://api.mailgun.net/v3/{cfg.mailgun_domain}/messages"
        data = {
            "from": cfg.from_address,
            "to": message.to,
            "subject": message.subject,
            "text": message.plain_text(),
            "html": message.html,
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, auth=("api", api_key), data=data)
                response.raise_for_status()
        except httpx.HTTPError:
            logger.exception("mailgun_send_failed", to=message.to, subject=message.subject)
            raise
        else:
            logger.info("mailgun_send_ok", to=message.to, subject=message.subject)
