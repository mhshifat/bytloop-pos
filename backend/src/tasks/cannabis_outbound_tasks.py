"""Celery tasks — cannabis compliance ledger → METRC/BioTrack (stub pipeline)."""

from __future__ import annotations

import asyncio

import structlog

from src.core.db import async_session_factory
from src.tasks.app import celery_app
from src.verticals.retail.cannabis.outbound import run_compliance_outbound_batch

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="src.tasks.cannabis_outbound_tasks.compliance_outbox_sync",
    autoretry_for=(),
    max_retries=0,
)
def compliance_outbox_sync() -> dict:  # type: ignore[no-untyped-def]
    """Drains a batch from ``cannabis_transactions`` (see ``CannabisConfig.compliance_outbound_mode``)."""

    async def _run() -> dict:
        async with async_session_factory() as session:
            return await run_compliance_outbound_batch(session)

    try:
        result = asyncio.run(_run())
    except Exception:
        logger.exception("cannabis_compliance_outbox_sync_failed")
        raise
    else:
        if result.get("processed"):
            logger.info("cannabis_compliance_outbox_sync_done", **result)
        return result
