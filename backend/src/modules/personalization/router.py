from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.modules.personalization.schemas import (
    CampaignTriggerRead,
    CampaignTriggerUpsert,
    SegmentMemberRead,
    SegmentRead,
    SegmentRecomputeResult,
)
from src.modules.personalization.service import PersonalizationService
from src.modules.audit.api import AuditService
from src.verticals.fnb.cafe_loyalty.entity import LoyaltyCard
from sqlalchemy import case, func, select, update

router = APIRouter(prefix="/personalization", tags=["personalization"])

@router.get(
    "/next-best-offers",
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def next_best_offers(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    product_id: UUID = Query(alias="productId"),
    limit: int = Query(default=5, ge=1, le=10),
) -> dict[str, object]:
    items = await PersonalizationService(db).next_best_offers(
        tenant_id=user.tenant_id, product_id=product_id, limit=limit
    )
    return {"productId": str(product_id), "items": items}


@router.get(
    "/segments",
    response_model=list[SegmentRead],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def list_segments(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[SegmentRead]:
    rows = await PersonalizationService(db).list_segments(tenant_id=user.tenant_id)
    return [SegmentRead.model_validate(r) for r in rows]


@router.get(
    "/segments/{segment_id}/members",
    response_model=list[SegmentMemberRead],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def segment_members(
    segment_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    limit: int = Query(default=200, ge=1, le=1000),
) -> list[SegmentMemberRead]:
    rows = await PersonalizationService(db).list_segment_members(
        tenant_id=user.tenant_id, segment_id=segment_id, limit=limit
    )
    return [
        SegmentMemberRead(
            customer_id=r.customer_id,
            score=float(r.score),
            meta=dict(r.meta or {}),
            refreshed_at=r.refreshed_at,
        )
        for r in rows
    ]


@router.post(
    "/segments/recompute",
    response_model=SegmentRecomputeResult,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def recompute_segments(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SegmentRecomputeResult:
    segments_created, memberships_written = await PersonalizationService(db).recompute_segments(
        tenant_id=user.tenant_id
    )
    return SegmentRecomputeResult(
        segments_created=segments_created, memberships_written=memberships_written
    )


@router.get(
    "/campaign-triggers",
    response_model=list[CampaignTriggerRead],
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def list_triggers(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[CampaignTriggerRead]:
    rows = await PersonalizationService(db).list_triggers(tenant_id=user.tenant_id)
    return [CampaignTriggerRead.model_validate(r) for r in rows]


@router.post(
    "/campaign-triggers",
    response_model=CampaignTriggerRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def upsert_trigger(
    data: CampaignTriggerUpsert,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CampaignTriggerRead:
    row = await PersonalizationService(db).upsert_trigger(
        tenant_id=user.tenant_id, trigger_id=None, data=data.model_dump()
    )
    return CampaignTriggerRead.model_validate(row)


@router.get(
    "/loyalty/auto-tune",
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def loyalty_auto_tune(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> dict[str, object]:
    # Compute current "typical" threshold and a simple recommendation.
    stmt = (
        select(
            func.count(LoyaltyCard.id),
            func.coalesce(func.avg(LoyaltyCard.punches_required), 0),
            func.sum(case((LoyaltyCard.free_items_earned > 0, 1), else_=0)),
        )
        .where(LoyaltyCard.tenant_id == user.tenant_id)
    )
    total, avg_req, earned_any = (await db.execute(stmt)).one()
    total_i = int(total or 0)
    earned_i = int(earned_any or 0)
    earned_rate = (earned_i / total_i) if total_i > 0 else 0.0
    current = int(round(float(avg_req or 0))) or 10

    if total_i < 20:
        recommended = current or 10
        reason = "Not enough loyalty history yet; keeping the current threshold."
    elif earned_rate < 0.2:
        recommended = max(5, min(20, current - 2))
        reason = "Low reward completion rate; lowering punches required should improve retention."
    elif earned_rate > 0.6:
        recommended = max(5, min(20, current + 2))
        reason = "High reward completion rate; increasing punches required may protect margin."
    else:
        recommended = current
        reason = "Current threshold looks balanced based on recent completions."

    return {
        "totalCards": total_i,
        "currentPunchesRequired": current,
        "recommendedPunchesRequired": recommended,
        "earnedRate": round(earned_rate, 4),
        "reason": reason,
    }


@router.post(
    "/loyalty/apply",
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def loyalty_apply(
    payload: dict[str, int],
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> dict[str, object]:
    new_req = int(payload.get("punchesRequired") or 0)
    if new_req < 1 or new_req > 100:
        return {"ok": False, "error": "punchesRequired must be 1..100"}

    # Snapshot current average for audit.
    current_avg = (
        await db.execute(
            select(func.coalesce(func.avg(LoyaltyCard.punches_required), 0)).where(
                LoyaltyCard.tenant_id == user.tenant_id
            )
        )
    ).scalar_one()

    res = await db.execute(
        update(LoyaltyCard)
        .where(LoyaltyCard.tenant_id == user.tenant_id)
        .values(punches_required=new_req)
        .execution_options(synchronize_session=False)
    )
    await AuditService(db).record(
        tenant_id=user.tenant_id,
        actor_id=user.id,
        action="loyalty.auto_tune.apply",
        resource_type="cafe_loyalty",
        resource_id=None,
        before={"avg_punches_required": float(current_avg or 0)},
        after={"punches_required": new_req},
    )
    return {"ok": True, "updated": int(res.rowcount or 0), "punchesRequired": new_req}

