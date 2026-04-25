"""Conversational POS assistant (limited tools, transcript-first).

This endpoint intentionally does not execute raw SQL or arbitrary actions.
It only calls a small, tenant-scoped tool set and returns a chat-like response.
"""

from __future__ import annotations

import json
from typing import Any, Literal

from fastapi import APIRouter, Depends, Request
from pydantic import Field

from src.core import cache
from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission, Role, permissions_for
from src.core.schemas import CamelModel
from src.core.errors import ValidationError
from src.integrations.ai.base import AIUnavailableError, Message
from src.integrations.ai.factory import get_ai_adapter
from src.modules.catalog.service import CatalogService
from src.modules.discounts.repository import DiscountRepository
from src.modules.reporting.service import ReportingService

router = APIRouter(prefix="/ai/assistant", tags=["ai-assistant"])


class AssistantChatRequest(CamelModel):
    message: str = Field(min_length=1, max_length=1500)


class AssistantChatResponse(CamelModel):
    reply: str
    tool: str | None = None
    tool_result: dict[str, Any] | None = None


def _client_ip(request: Request) -> str:
    real = getattr(request.state, "real_ip", None)
    if isinstance(real, str) and real:
        return real
    if request.client:
        return request.client.host
    return "unknown"


async def _rate_limit_ok(ip: str) -> bool:
    """60 assistant calls / minute / IP. Redis down = fail open."""
    key = f"pos:rl:assistant:{ip}"
    raw = await cache.get_str(key)
    count = int(raw) if raw and raw.isdigit() else 0
    if count >= 60:
        return False
    await cache.set_str(key, str(count + 1), ttl_seconds=60)
    return True


@router.post(
    "/chat",
    response_model=AssistantChatResponse,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def chat(
    req: AssistantChatRequest,
    request: Request,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> AssistantChatResponse:
    adapter = get_ai_adapter()
    if not adapter.is_enabled():
        raise AIUnavailableError("AI provider is disabled.")

    ip = _client_ip(request)
    if not await _rate_limit_ok(ip):
        raise ValidationError("Too many requests. Please wait a moment and try again.")

    roles = [Role(r) for r in user.roles if r in Role.__members__.values()]
    granted = permissions_for(roles)
    can_reports = Permission.REPORTS_VIEW in granted
    can_products = Permission.PRODUCTS_READ in granted

    tool_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": [
                    "search_products",
                    "list_top_products",
                    "check_discount_code",
                    "explain_anomaly",
                    "respond",
                ],
            },
            "args": {"type": "object"},
            "reply": {"type": "string"},
        },
        "required": ["action", "args", "reply"],
    }

    sys = (
        "You are a POS assistant for cashiers.\n"
        "You MUST pick one action from the allowed tool set.\n"
        "Rules:\n"
        "- Never ask for secrets.\n"
        "- Never output PII.\n"
        "- If the user asks for something outside tools, use action=respond.\n"
        "- Use action=search_products for 'find' queries.\n"
        "- Use action=list_top_products for 'best selling' questions.\n"
        "- Use action=check_discount_code to validate a discount code (no applying).\n"
        "- Use action=explain_anomaly only if you have enough info; otherwise respond.\n"
        "Return ONLY JSON matching the schema."
    )

    result = await adapter.structured(
        messages=[
            Message(role="system", content=sys),
            Message(role="user", content=req.message.strip()),
        ],
        json_schema=tool_schema,
        temperature=0.2,
        max_tokens=500,
    )

    action: str = str(result.get("action", "respond"))
    args: dict[str, Any] = result.get("args") if isinstance(result.get("args"), dict) else {}
    reply: str = str(result.get("reply", "")).strip() or "Okay."

    if action == "search_products":
        if not can_products:
            return AssistantChatResponse(reply="You don’t have access to search products.", tool=None)
        q = str(args.get("query", "")).strip()
        if not q:
            return AssistantChatResponse(reply="What should I search for?", tool=None)
        rows, _ = await CatalogService(db).list_products(
            tenant_id=user.tenant_id, search=q, category_id=None, page=1, page_size=10
        )
        items = [
            {
                "productId": str(p.id),
                "name": p.name,
                "sku": p.sku,
                "priceCents": p.price_cents,
                "currency": p.currency,
            }
            for p in rows
        ]
        return AssistantChatResponse(reply=reply, tool="search_products", tool_result={"items": items})

    if action == "list_top_products":
        if not can_reports:
            return AssistantChatResponse(reply="You don’t have access to reports.", tool=None)
        days_raw = args.get("days", 30)
        try:
            days = int(days_raw)
        except Exception:  # noqa: BLE001
            days = 30
        days = min(365, max(1, days))
        items = await ReportingService(db).top_products(tenant_id=user.tenant_id, days=days, limit=10)
        return AssistantChatResponse(reply=reply, tool="list_top_products", tool_result={"days": days, "items": items})

    if action == "check_discount_code":
        code = str(args.get("code", "")).strip().upper()
        if not code:
            return AssistantChatResponse(reply="What discount code should I check?", tool=None)
        disc = await DiscountRepository(db).by_code(tenant_id=user.tenant_id, code=code)
        ok = disc is not None
        return AssistantChatResponse(
            reply=reply,
            tool="check_discount_code",
            tool_result={"code": code, "valid": ok},
        )

    if action == "explain_anomaly":
        if not can_reports:
            return AssistantChatResponse(reply="You don’t have access to reports.", tool=None)
        # v1: No direct anomaly tool plumbing here yet; provide a safe answer.
        return AssistantChatResponse(
            reply=reply,
            tool="explain_anomaly",
            tool_result={"note": "Anomaly explanations are available in AI Reports; ask in /ai-insights."},
        )

    return AssistantChatResponse(reply=reply, tool=None, tool_result=None)

