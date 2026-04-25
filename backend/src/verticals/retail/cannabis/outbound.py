"""METRC/BioTrack-style outbound sync — worker entry (stub implementation).

Real state traceability APIs are jurisdiction-specific. This module implements
the process loop: dequeue from ``cannabis_transactions`` outbox, log, optionally
mark success for dev, and (later) POST to configured vendor bases.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from src.core.config import settings
from src.verticals.retail.cannabis.service import CannabisService

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.ext.asyncio import AsyncSession

    from src.verticals.retail.cannabis.entity import CannabisTransaction

logger = structlog.get_logger(__name__)


def _txn_payload(txn: CannabisTransaction) -> dict[str, Any]:
    return {
        "transaction_id": str(txn.id),
        "tenant_id": str(txn.tenant_id),
        "batch_id": str(txn.batch_id),
        "kind": txn.kind,
        "grams_delta": float(txn.grams_delta),
        "order_id": str(txn.order_id) if txn.order_id else None,
        "customer_id": str(txn.customer_id) if txn.customer_id else None,
    }


async def run_compliance_outbound_batch(session: AsyncSession) -> dict[str, Any]:
    """Run one batch per ``settings.cannabis.compliance_outbound_*`` config."""
    cfg = settings.cannabis
    mode = cfg.compliance_outbound_mode
    if mode == "off":
        return {"mode": mode, "processed": 0, "skipped": "mode_off"}

    service = CannabisService(session)
    batch = await service.pending_outbound_all_tenants(
        limit=cfg.compliance_outbound_batch_size
    )
    if not batch:
        return {"mode": mode, "processed": 0, "pending": 0}

    target = cfg.compliance_outbound_target
    processed = 0
    for txn in batch:
        payload = _txn_payload(txn)
        if mode == "log":
            logger.info(
                "cannabis_compliance_outbox_log",
                target=target,
                **payload,
            )
            processed += 1
            continue
        if mode == "noop_success":
            logger.info(
                "cannabis_compliance_outbox_noop_success",
                target=target,
                **payload,
            )
            await service.mark_synced(
                tenant_id=txn.tenant_id, transaction_id=txn.id
            )
            processed += 1
            continue

    await session.commit()
    return {
        "mode": mode,
        "processed": processed,
        "target": target,
    }


# Kept for tests and future single-transaction retry APIs.
async def run_compliance_outbound_for_tenant(
    session: AsyncSession, *, tenant_id: UUID, limit: int
) -> dict[str, Any]:
    """Process pending rows for one tenant (same mode semantics as global batch)."""
    cfg = settings.cannabis
    mode = cfg.compliance_outbound_mode
    if mode == "off":
        return {"mode": mode, "processed": 0, "skipped": "mode_off"}

    service = CannabisService(session)
    rows = await service.unsynced_transactions(tenant_id=tenant_id)
    rows = rows[: max(1, min(limit, 500))]
    if not rows:
        return {"mode": mode, "processed": 0, "pending": 0}

    target = cfg.compliance_outbound_target
    processed = 0
    for txn in rows:
        payload = _txn_payload(txn)
        if mode == "log":
            logger.info(
                "cannabis_compliance_outbox_log",
                target=target,
                **payload,
            )
            processed += 1
        elif mode == "noop_success":
            logger.info(
                "cannabis_compliance_outbox_noop_success",
                target=target,
                **payload,
            )
            await service.mark_synced(
                tenant_id=tenant_id, transaction_id=txn.id
            )
            processed += 1

    await session.commit()
    return {"mode": mode, "processed": processed, "target": target}
