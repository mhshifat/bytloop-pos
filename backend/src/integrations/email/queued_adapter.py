"""Adapter that enqueues to Celery instead of sending inline.

Use this in production to keep email-sending latency off the request path.
``get_email_adapter()`` returns this when the config opts into async sending.
"""

from __future__ import annotations

import structlog

from src.integrations.email.base import EmailAdapter, EmailMessage

logger = structlog.get_logger(__name__)


class QueuedEmailAdapter(EmailAdapter):
    """Delegates the real send to a Celery task."""

    async def send(self, message: EmailMessage) -> None:
        # Imported lazily so importing this module doesn't start the Celery app.
        from src.tasks.email_tasks import enqueue_email

        enqueue_email(
            to=message.to,
            subject=message.subject,
            html=message.html,
            text=message.plain_text(),
        )
        logger.info("email_enqueued", to=message.to, subject=message.subject)
