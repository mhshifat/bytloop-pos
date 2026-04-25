"""WebSocket endpoint that streams KDS events.

The frontend subscribes with ``?tenant=…&station=kitchen`` and receives
``{id: ticketId}`` messages — tiny payloads that tell the client which
ticket to re-fetch via REST.
"""

from __future__ import annotations

from uuid import UUID

import structlog
from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.core.realtime import subscribe

logger = structlog.get_logger(__name__)

router = APIRouter()


@router.websocket("/ws/restaurant/kds")
async def kds_stream(
    websocket: WebSocket,
    tenant_id: UUID = Query(alias="tenant"),
    station: str = Query(default="kitchen"),
) -> None:
    await websocket.accept()
    topic = f"kds:{station}"
    try:
        async for message in subscribe(tenant_id, topic):
            await websocket.send_json(message)
    except WebSocketDisconnect:
        logger.info("kds_ws_disconnect", tenant_id=str(tenant_id), station=station)
    except Exception:
        logger.exception("kds_ws_error", tenant_id=str(tenant_id))
        await websocket.close(code=1011)
