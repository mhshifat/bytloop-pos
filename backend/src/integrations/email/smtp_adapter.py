"""SMTP adapter — used for local dev (MailHog) and as a fallback in prod."""

from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage as StdEmailMessage

import structlog

from src.core.config import settings
from src.integrations.email.base import EmailAdapter, EmailMessage

logger = structlog.get_logger(__name__)


class SmtpEmailAdapter(EmailAdapter):
    """Sends via plain SMTP. Blocking smtplib work runs in a thread."""

    async def send(self, message: EmailMessage) -> None:
        await asyncio.to_thread(self._send_sync, message)

    def _send_sync(self, message: EmailMessage) -> None:
        cfg = settings.email
        std = StdEmailMessage()
        std["From"] = cfg.from_address
        std["To"] = message.to
        std["Subject"] = message.subject
        std.set_content(message.plain_text())
        std.add_alternative(message.html, subtype="html")

        try:
            with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=10) as smtp:
                if cfg.smtp_use_tls:
                    smtp.starttls()
                if cfg.smtp_user and cfg.smtp_password.get_secret_value():
                    smtp.login(cfg.smtp_user, cfg.smtp_password.get_secret_value())
                smtp.send_message(std)
        except Exception:
            logger.exception("smtp_send_failed", to=message.to, subject=message.subject)
            raise
        else:
            logger.info("smtp_send_ok", to=message.to, subject=message.subject)
