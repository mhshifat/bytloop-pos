"""Celery tasks for AI analytics (anomalies + forecast accuracy).

These run out-of-band so heavy ML work never blocks API requests.
They emit lightweight alerts via Redis realtime pub/sub so the UI (or a
future plugin) can surface them.
"""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime

import structlog
from sqlalchemy import select

from src.core.db import async_session_factory
from src.core.realtime import publish
from src.modules.ai.service import AIAnalyticsService
from src.modules.tenants.entity import Tenant
from src.tasks.app import celery_app

logger = structlog.get_logger(__name__)


@celery_app.task(
    name="src.tasks.ai_analytics_tasks.scan_anomalies",
    autoretry_for=(),
    max_retries=0,
)
def scan_anomalies() -> dict:  # type: ignore[no-untyped-def]
    """Scan every tenant for recent revenue anomalies and publish alerts."""

    async def _run() -> dict:
        async with async_session_factory() as session:
            tenants = list((await session.execute(select(Tenant.id))).scalars().all())
            service = AIAnalyticsService(session)
            alerts = 0
            for tid in tenants:
                rows = await service.detect_demand_anomalies(tenant_id=tid, window_days=60)
                if not rows:
                    continue
                # Publish only the top few anomalies by severity.
                top = sorted(rows, key=lambda r: r[2], reverse=True)[:5]
                await publish(
                    tid,
                    "ai-alerts",
                    {
                        "kind": "demand_anomalies",
                        "generatedAt": datetime.now(tz=UTC).isoformat(),
                        "anomalies": [
                            {
                                "timestamp": ts.isoformat(),
                                "revenueCents": cents,
                                "severity": round(float(sev), 3),
                            }
                            for ts, cents, sev in top
                        ],
                    },
                )
                alerts += 1
            return {"tenants": len(tenants), "alerts": alerts}

    try:
        result = asyncio.run(_run())
    except Exception:
        logger.exception("ai_anomaly_scan_failed")
        raise
    else:
        if result.get("alerts"):
            logger.info("ai_anomaly_scan_done", **result)
        return result


@celery_app.task(
    name="src.tasks.ai_analytics_tasks.forecast_accuracy",
    autoretry_for=(),
    max_retries=0,
)
def forecast_accuracy() -> dict:  # type: ignore[no-untyped-def]
    """Evaluate forecast accuracy per tenant and publish summary."""

    async def _run() -> dict:
        async with async_session_factory() as session:
            tenants = list((await session.execute(select(Tenant.id))).scalars().all())
            service = AIAnalyticsService(session)
            published = 0
            for tid in tenants:
                mape = await service.evaluate_forecasters(
                    tenant_id=tid, holdout_days=7, history_days=120
                )
                await publish(
                    tid,
                    "ai-alerts",
                    {
                        "kind": "forecast_accuracy",
                        "generatedAt": datetime.now(tz=UTC).isoformat(),
                        "mape": mape,
                    },
                )
                published += 1
            return {"tenants": len(tenants), "published": published}

    try:
        result = asyncio.run(_run())
    except Exception:
        logger.exception("ai_forecast_accuracy_failed")
        raise
    else:
        logger.info("ai_forecast_accuracy_done", **result)
        return result

