from __future__ import annotations

from datetime import UTC, datetime, timedelta

import structlog
from sqlalchemy import select

from src.core.db import get_session
from src.modules.ai.service import AIAnalyticsService
from src.modules.customers.entity import Customer
from src.modules.personalization.entity import CampaignDelivery, CampaignTrigger
from src.tasks.app import celery_app
from src.tasks.email_tasks import enqueue_email

logger = structlog.get_logger(__name__)


@celery_app.task(name="src.tasks.personalization_tasks.churn_email_cadence")
def churn_email_cadence() -> str:
    """Send churn-risk emails for enabled triggers.

    Runs in Celery beat. Uses DB delivery log to enforce cooldown per customer.
    """

    async def _run() -> tuple[int, int]:
        sent = 0
        considered = 0
        async for session in get_session():  # type: ignore[misc]
            # Find enabled email triggers.
            triggers = (
                await session.execute(
                    select(CampaignTrigger).where(
                        CampaignTrigger.enabled.is_(True),
                        CampaignTrigger.channel == "email",
                    )
                )
            ).scalars().all()
            now = datetime.now(tz=UTC)
            for trig in triggers:
                # Pull churn risk list using existing model logic.
                rows = await AIAnalyticsService(session).customers_at_churn_risk(
                    tenant_id=trig.tenant_id, threshold=float(trig.threshold)
                )
                for r in rows[:500]:
                    considered += 1
                    cid = r["customer_id"]
                    email = r.get("email")
                    if not email:
                        continue
                    # Cooldown check.
                    log = (
                        await session.execute(
                            select(CampaignDelivery).where(
                                CampaignDelivery.tenant_id == trig.tenant_id,
                                CampaignDelivery.trigger_id == trig.id,
                                CampaignDelivery.customer_id == cid,
                            )
                        )
                    ).scalar_one_or_none()
                    if log is not None and log.last_sent_at > now - timedelta(days=int(trig.cooldown_days)):
                        continue

                    subject = trig.subject or "We miss you — come back today"
                    html = trig.html_template or "<p>Come back and enjoy your next visit.</p>"
                    if trig.discount_code:
                        html += f"<p>Use discount code <b>{trig.discount_code}</b>.</p>"

                    enqueue_email(to=email, subject=subject, html=html, text=None)
                    if log is None:
                        session.add(
                            CampaignDelivery(
                                tenant_id=trig.tenant_id,
                                trigger_id=trig.id,
                                customer_id=cid,
                                last_sent_at=now,
                            )
                        )
                    else:
                        log.last_sent_at = now
                    await session.flush()
                    sent += 1
            return sent, considered
        return 0, 0

    import asyncio  # noqa: PLC0415

    sent, considered = asyncio.run(_run())
    logger.info("churn_email_cadence_done", sent=sent, considered=considered)
    return "ok"

