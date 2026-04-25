"""Email-sending Celery tasks.

Keeps SMTP / Mailgun latency off the request path. Services enqueue via
``send_activation_email.delay(...)``; the worker picks it up and calls the
current EmailAdapter (Strategy).
"""

from __future__ import annotations

import asyncio

import structlog

from src.integrations.email.base import EmailMessage
from src.integrations.email.factory import get_direct_email_adapter
from src.tasks.app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="src.tasks.email_tasks.send_email",
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=300,
    retry_jitter=True,
    max_retries=5,
)
def send_email_task(self, *, to: str, subject: str, html: str, text: str | None) -> None:  # type: ignore[no-untyped-def]
    """Generic envelope sender — exposed through higher-level helpers below."""
    message = EmailMessage(to=to, subject=subject, html=html, text=text)
    try:
        asyncio.run(get_direct_email_adapter().send(message))
    except Exception as exc:
        logger.exception("send_email_task_failed", to=to, subject=subject)
        raise self.retry(exc=exc) from exc


@celery_app.task(name="src.tasks.email_tasks.noop_healthcheck")
def noop_healthcheck() -> str:
    """Beat-scheduled heartbeat so we can see the worker is alive in logs."""
    logger.info("celery_beat_heartbeat")
    return "ok"


def enqueue_email(*, to: str, subject: str, html: str, text: str | None = None) -> None:
    """Module-level helper for services to enqueue without importing Celery symbols."""
    send_email_task.delay(to=to, subject=subject, html=html, text=text)
