from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.services.garage.schemas import (
    JobCardCreate,
    JobCardRead,
    JobLineCreate,
    JobLineRead,
    JobTotalsRead,
    UpdateJobStatusRequest,
    VehicleCreate,
    VehicleHistoryItem,
    VehicleRead,
)
from src.verticals.services.garage.service import GarageService

router = APIRouter(prefix="/garage", tags=["garage"])


@router.get(
    "/vehicles",
    response_model=list[VehicleRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_vehicles(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[VehicleRead]:
    rows = await GarageService(db).list_vehicles(tenant_id=user.tenant_id)
    return [VehicleRead.model_validate(v) for v in rows]


@router.post(
    "/vehicles",
    response_model=VehicleRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def register_vehicle(
    data: VehicleCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> VehicleRead:
    vehicle = await GarageService(db).register_vehicle(
        tenant_id=user.tenant_id,
        customer_id=data.customer_id,
        plate=data.plate,
        make=data.make,
        model=data.model,
        year=data.year,
        vin=data.vin,
    )
    return VehicleRead.model_validate(vehicle)


@router.get(
    "/jobs",
    response_model=list[JobCardRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_jobs(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[JobCardRead]:
    rows = await GarageService(db).list_open_jobs(tenant_id=user.tenant_id)
    return [JobCardRead.model_validate(j) for j in rows]


@router.post(
    "/jobs",
    response_model=JobCardRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def open_job(
    data: JobCardCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> JobCardRead:
    job = await GarageService(db).open_job(
        tenant_id=user.tenant_id,
        vehicle_id=data.vehicle_id,
        description=data.description,
        technician_id=data.technician_id,
    )
    return JobCardRead.model_validate(job)


@router.patch(
    "/jobs/{job_id}/status",
    response_model=JobCardRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def update_job_status(
    job_id: UUID,
    data: UpdateJobStatusRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> JobCardRead:
    job = await GarageService(db).update_job_status(
        tenant_id=user.tenant_id, job_id=job_id, status=data.status
    )
    return JobCardRead.model_validate(job)


@router.get(
    "/jobs/{job_id}/lines",
    response_model=list[JobLineRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_job_lines(
    job_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[JobLineRead]:
    rows = await GarageService(db).list_lines(tenant_id=user.tenant_id, job_id=job_id)
    return [JobLineRead.model_validate(r) for r in rows]


@router.post(
    "/jobs/{job_id}/lines",
    response_model=JobLineRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def add_job_line(
    job_id: UUID,
    data: JobLineCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> JobLineRead:
    line = await GarageService(db).add_line(
        tenant_id=user.tenant_id,
        job_id=job_id,
        kind=data.kind,
        description=data.description,
        quantity=data.quantity,
        unit_cost_cents=data.unit_cost_cents,
        product_id=data.product_id,
    )
    return JobLineRead.model_validate(line)


@router.delete(
    "/jobs/{job_id}/lines/{line_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def remove_job_line(
    job_id: UUID,
    line_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> None:
    await GarageService(db).remove_line(tenant_id=user.tenant_id, line_id=line_id)


@router.get(
    "/jobs/{job_id}/totals",
    response_model=JobTotalsRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def job_totals(
    job_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> JobTotalsRead:
    totals = await GarageService(db).job_totals(
        tenant_id=user.tenant_id, job_id=job_id
    )
    return JobTotalsRead(
        parts_cents=totals["partsCents"],
        labor_cents=totals["laborCents"],
        total_cents=totals["totalCents"],
    )


@router.get(
    "/vehicles/{vehicle_id}/history",
    response_model=list[VehicleHistoryItem],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def vehicle_history(
    vehicle_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[VehicleHistoryItem]:
    rows = await GarageService(db).vehicle_history(
        tenant_id=user.tenant_id, vehicle_id=vehicle_id
    )
    return [VehicleHistoryItem.model_validate(r) for r in rows]
