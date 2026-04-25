"""Email adapter factory — selects provider by config.

``get_email_adapter`` honors ``EMAIL_ASYNC_SEND`` — when true, returns a
QueuedEmailAdapter that hands off to Celery. The worker itself uses
``_direct_adapter()`` which always returns the concrete provider.
"""

from __future__ import annotations

import os
from functools import lru_cache

from src.core.config import settings
from src.integrations.email.base import EmailAdapter
from src.integrations.email.mailgun_adapter import MailgunEmailAdapter
from src.integrations.email.queued_adapter import QueuedEmailAdapter
from src.integrations.email.smtp_adapter import SmtpEmailAdapter


def _direct_adapter() -> EmailAdapter:
    provider = settings.email.provider
    if provider == "smtp":
        return SmtpEmailAdapter()
    if provider == "mailgun":
        return MailgunEmailAdapter()
    if provider == "sendgrid":
        raise NotImplementedError("SendGrid adapter stub — implement when needed")
    raise ValueError(f"Unknown email provider: {provider}")


@lru_cache(maxsize=1)
def get_email_adapter() -> EmailAdapter:
    if os.environ.get("EMAIL_ASYNC_SEND", "false").lower() == "true":
        return QueuedEmailAdapter()
    return _direct_adapter()


@lru_cache(maxsize=1)
def get_direct_email_adapter() -> EmailAdapter:
    """Used by Celery workers — always the concrete provider."""
    return _direct_adapter()
