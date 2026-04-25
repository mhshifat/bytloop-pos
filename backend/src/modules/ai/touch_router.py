"""Campaign-touch capture endpoint.

Public (no auth required) — UTM capture happens *before* signup by design;
that's the whole point of attribution. Tenant is identified by slug in the
payload so the row lands in the right tenant's bucket. A handful of
guardrails keep this from being abused:

* Per-IP rate limit (20/min) via the existing ``cache`` wrapper.
* Channel/source/medium/campaign length caps so a malicious client can't
  fill the table with 10KB blobs.
* Tenant slug must resolve to a real tenant; we silently drop the touch
  (200 OK) if it doesn't — no tenant enumeration via error messages.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import Field
from sqlalchemy import select

from src.core import cache
from src.core.deps import DbSession
from src.core.schemas import CamelModel
from src.modules.ai.entity import CampaignTouch
from src.modules.tenants.entity import Tenant

router = APIRouter(prefix="/campaign-touches", tags=["attribution"])


class CampaignTouchCreate(CamelModel):
    tenant_slug: str = Field(min_length=1, max_length=64)
    channel: str = Field(min_length=1, max_length=64)
    source: str | None = Field(default=None, max_length=64)
    medium: str | None = Field(default=None, max_length=64)
    campaign: str | None = Field(default=None, max_length=128)
    landing_page: str | None = Field(default=None, max_length=255)
    # Optional — only set after signup. When omitted we still write the
    # touch (anonymous visit) so the sign-up handler can associate it later.
    customer_id: UUID | None = None


async def _rate_limit_ok(ip: str) -> bool:
    """20 touches per IP per minute. Redis down = fail open (not a security
    boundary, just abuse mitigation)."""
    key = f"pos:utm:rl:{ip}"
    count_raw = await cache.get_str(key)
    count = int(count_raw) if count_raw and count_raw.isdigit() else 0
    if count >= 20:
        return False
    await cache.set_str(key, str(count + 1), ttl_seconds=60)
    return True


@router.post("", status_code=204)
async def record_touch(
    data: CampaignTouchCreate,
    request: Request,
    db: DbSession,
) -> None:
    """Record one attribution touch. Returns 204 even when we silently drop
    (unknown tenant, rate-limited) so the client can fire-and-forget."""
    ip = request.client.host if request.client else "unknown"
    if not await _rate_limit_ok(ip):
        return None

    tenant = (
        await db.execute(
            select(Tenant).where(Tenant.slug == data.tenant_slug.lower())
        )
    ).scalar_one_or_none()
    if tenant is None:
        # Silent drop — enumeration protection.
        return None

    touch = CampaignTouch(
        tenant_id=tenant.id,
        customer_id=data.customer_id,
        channel=data.channel,
        source=data.source,
        medium=data.medium,
        campaign=data.campaign,
        landing_page=data.landing_page,
    )
    db.add(touch)
    await db.flush()
    return None
