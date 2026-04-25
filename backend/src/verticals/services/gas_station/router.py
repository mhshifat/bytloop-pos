from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.services.gas_station.schemas import (
    DispenserReadingCreate,
    DispenserReadingRead,
    FuelDispenserCreate,
    FuelDispenserRead,
)
from src.verticals.services.gas_station.service import GasStationService

router = APIRouter(prefix="/gas-station", tags=["gas-station"])


@router.get(
    "/dispensers",
    response_model=list[FuelDispenserRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_dispensers(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[FuelDispenserRead]:
    rows = await GasStationService(db).list_dispensers(tenant_id=user.tenant_id)
    return [FuelDispenserRead.model_validate(r) for r in rows]


@router.post(
    "/dispensers",
    response_model=FuelDispenserRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def create_dispenser(
    data: FuelDispenserCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> FuelDispenserRead:
    dispenser = await GasStationService(db).create_dispenser(
        tenant_id=user.tenant_id,
        label=data.label,
        fuel_type=data.fuel_type,
        price_per_liter_cents=data.price_per_liter_cents,
        product_id=data.product_id,
    )
    return FuelDispenserRead.model_validate(dispenser)


@router.post(
    "/readings",
    response_model=DispenserReadingRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def record_reading(
    data: DispenserReadingCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DispenserReadingRead:
    reading = await GasStationService(db).record_reading(
        tenant_id=user.tenant_id,
        cashier_id=user.id,
        dispenser_id=data.dispenser_id,
        totalizer_reading=data.totalizer_reading,
    )
    return DispenserReadingRead.model_validate(reading)


@router.get(
    "/dispensers/{dispenser_id}/readings",
    response_model=list[DispenserReadingRead],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def list_readings(
    dispenser_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[DispenserReadingRead]:
    rows = await GasStationService(db).list_readings(
        tenant_id=user.tenant_id, dispenser_id=dispenser_id
    )
    return [DispenserReadingRead.model_validate(r) for r in rows]
