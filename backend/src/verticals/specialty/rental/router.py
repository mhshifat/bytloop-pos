from __future__ import annotations

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.specialty.rental.schemas import (
    AssetCreate,
    AssetRead,
    ContractCreate,
    ContractRead,
    ReturnRequest,
    ReturnSummaryRead,
)
from src.verticals.specialty.rental.service import RentalService

router = APIRouter(prefix="/rental", tags=["rental"])


@router.get(
    "/assets",
    response_model=list[AssetRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_assets(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[AssetRead]:
    rows = await RentalService(db).list_assets(tenant_id=user.tenant_id)
    return [AssetRead.model_validate(r) for r in rows]


@router.get(
    "/assets/available",
    response_model=list[AssetRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def available_assets(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    starts_at: datetime = Query(..., alias="startsAt"),
    ends_at: datetime = Query(..., alias="endsAt"),
) -> list[AssetRead]:
    rows = await RentalService(db).available_assets(
        tenant_id=user.tenant_id, starts_at=starts_at, ends_at=ends_at
    )
    return [AssetRead.model_validate(r) for r in rows]


@router.post(
    "/assets",
    response_model=AssetRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def add_asset(
    data: AssetCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> AssetRead:
    asset = await RentalService(db).add_asset(
        tenant_id=user.tenant_id,
        code=data.code,
        label=data.label,
        hourly_rate_cents=data.hourly_rate_cents,
        daily_rate_cents=data.daily_rate_cents,
    )
    return AssetRead.model_validate(asset)


@router.get(
    "/contracts",
    response_model=list[ContractRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_contracts(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[ContractRead]:
    rows = await RentalService(db).list_contracts(tenant_id=user.tenant_id)
    return [ContractRead.model_validate(r) for r in rows]


@router.post(
    "/contracts",
    response_model=ContractRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def reserve(
    data: ContractCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ContractRead:
    contract = await RentalService(db).reserve(
        tenant_id=user.tenant_id,
        asset_id=data.asset_id,
        customer_id=data.customer_id,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        deposit_cents=data.deposit_cents,
    )
    return ContractRead.model_validate(contract)


@router.post(
    "/contracts/{contract_id}/check-out",
    response_model=ContractRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def check_out_asset(
    contract_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ContractRead:
    """Hand the asset to the customer — RESERVED → OUT."""
    contract = await RentalService(db).mark_out(
        tenant_id=user.tenant_id, contract_id=contract_id
    )
    return ContractRead.model_validate(contract)


@router.post(
    "/contracts/{contract_id}/return",
    response_model=ReturnSummaryRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def return_asset(
    contract_id: UUID,
    data: ReturnRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ReturnSummaryRead:
    """Process return with late + damage fees, deposit offset, net due."""
    contract, summary = await RentalService(db).process_return(
        tenant_id=user.tenant_id,
        contract_id=contract_id,
        returned_at=data.returned_at,
        damage_fee_cents=data.damage_fee_cents,
        damage_notes=data.damage_notes,
    )
    return ReturnSummaryRead(
        contract=ContractRead.model_validate(contract),
        base_rental_cents=summary.base_rental_cents,
        late_fee_cents=summary.late_fee_cents,
        damage_fee_cents=summary.damage_fee_cents,
        deposit_refund_cents=summary.deposit_refund_cents,
        net_due_cents=summary.net_due_cents,
    )
