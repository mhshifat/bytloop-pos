from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.modules.shifts.schemas import CloseShiftRequest, OpenShiftRequest, ShiftRead
from src.modules.shifts.service import ShiftService

router = APIRouter(prefix="/shifts", tags=["shifts"])


@router.get("/current", response_model=ShiftRead | None, dependencies=[Depends(requires(Permission.ORDERS_CREATE))])
async def current_shift(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ShiftRead | None:
    shift = await ShiftService(db).current(tenant_id=user.tenant_id, cashier_id=user.id)
    return ShiftRead.model_validate(shift) if shift else None


@router.post(
    "/open",
    response_model=ShiftRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def open_shift(
    req: OpenShiftRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ShiftRead:
    shift = await ShiftService(db).open(
        tenant_id=user.tenant_id,
        cashier_id=user.id,
        opening_float_cents=req.opening_float_cents,
    )
    return ShiftRead.model_validate(shift)


@router.post(
    "/close",
    response_model=ShiftRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def close_shift(
    req: CloseShiftRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ShiftRead:
    shift = await ShiftService(db).close(
        tenant_id=user.tenant_id,
        cashier_id=user.id,
        closing_counted_cents=req.closing_counted_cents,
    )
    return ShiftRead.model_validate(shift)
