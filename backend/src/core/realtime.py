"""Lightweight WebSocket pub/sub over Redis.

Used by the KDS screen (and any future real-time feature) to push updates
without the client polling. Messages are tiny (IDs only — the client fetches
fresh data via REST) so the 20 MB Redis ceiling stays safe.

See docs/PLAN.md §14 Real-time and §15b Redis budget.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from uuid import UUID

import redis.asyncio as redis
import structlog

from src.core.config import settings

logger = structlog.get_logger(__name__)


def _channel(tenant_id: UUID, topic: str) -> str:
    return f"pos:rt:{tenant_id}:{topic}"


async def publish(tenant_id: UUID, topic: str, payload: dict[str, object]) -> None:
    client = redis.Redis.from_url(
        settings.redis.url,
        socket_timeout=settings.redis.op_timeout_seconds,
    )
    try:
        await client.publish(_channel(tenant_id, topic), json.dumps(payload))
    except Exception:
        logger.warning("realtime_publish_failed", tenant_id=str(tenant_id), topic=topic)
    finally:
        await client.close()


async def subscribe(
    tenant_id: UUID, topic: str
) -> AsyncIterator[dict[str, object]]:
    client = redis.Redis.from_url(
        settings.redis.url,
        socket_timeout=settings.redis.op_timeout_seconds,
    )
    pubsub = client.pubsub()
    await pubsub.subscribe(_channel(tenant_id, topic))
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=5.0)
            if message is None:
                # Keep the loop alive; client pings surface via WebSocket frames.
                await asyncio.sleep(0.1)
                continue
            data = message.get("data")
            if isinstance(data, (bytes, bytearray)):
                try:
                    yield json.loads(data.decode("utf-8"))
                except json.JSONDecodeError:
                    continue
    finally:
        await pubsub.unsubscribe()
        await pubsub.close()
        await client.close()
