from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.services.rfid_memberships.schemas import (
    IssuePassRequest,
    PassUseRead,
    RedeemRequest,
    RedeemResult,
    RfidPassRead,
    UpdatePassStatusRequest,
)
from src.verticals.services.rfid_memberships.service import RfidMembershipsService

router = APIRouter(prefix="/rfid", tags=["rfid-memberships"])


@router.get(
    "/passes",
    response_model=list[RfidPassRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_passes(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[RfidPassRead]:
    rows = await RfidMembershipsService(db).list_passes(tenant_id=user.tenant_id)
    return [RfidPassRead.model_validate(r) for r in rows]


@router.post(
    "/passes",
    response_model=RfidPassRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def issue_pass(
    data: IssuePassRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> RfidPassRead:
    pass_ = await RfidMembershipsService(db).issue_pass(
        tenant_id=user.tenant_id,
        rfid_tag=data.rfid_tag,
        customer_id=data.customer_id,
        plan_code=data.plan_code,
        balance_uses=data.balance_uses,
        expires_on=data.expires_on,
    )
    return RfidPassRead.model_validate(pass_)


@router.patch(
    "/passes/{pass_id}/status",
    response_model=RfidPassRead,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def update_pass_status(
    pass_id: UUID,
    data: UpdatePassStatusRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> RfidPassRead:
    pass_ = await RfidMembershipsService(db).update_status(
        tenant_id=user.tenant_id, pass_id=pass_id, status=data.status
    )
    return RfidPassRead.model_validate(pass_)


@router.post(
    "/redeem",
    response_model=RedeemResult,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def redeem_pass(
    data: RedeemRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> RedeemResult:
    outcome = await RfidMembershipsService(db).redeem(
        tenant_id=user.tenant_id, rfid_tag=data.rfid_tag, location=data.location
    )
    return RedeemResult(
        success=outcome.success,
        reason=outcome.reason,
        pass_id=outcome.pass_id,
        balance_uses_remaining=outcome.balance_uses_remaining,
    )


@router.get(
    "/passes/{pass_id}/transactions",
    response_model=list[PassUseRead],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def transactions_for_pass(
    pass_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[PassUseRead]:
    rows = await RfidMembershipsService(db).transactions_for_pass(
        tenant_id=user.tenant_id, pass_id=pass_id
    )
    return [PassUseRead.model_validate(r) for r in rows]
