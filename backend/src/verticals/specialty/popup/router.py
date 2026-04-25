from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.specialty.popup.schemas import (
    PopupCloseReport,
    PopupEventCreate,
    PopupEventRead,
    PopupInventorySnapshotRead,
    PopupSoldLine,
    PopupStallCreate,
    PopupStallRead,
)
from src.verticals.specialty.popup.service import PopupService

router = APIRouter(prefix="/popup", tags=["popup"])


@router.get(
    "/events",
    response_model=list[PopupEventRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_events(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[PopupEventRead]:
    rows = await PopupService(db).list_events(tenant_id=user.tenant_id)
    return [PopupEventRead.model_validate(r) for r in rows]


@router.post(
    "/events",
    response_model=PopupEventRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def create_event(
    data: PopupEventCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PopupEventRead:
    event = await PopupService(db).create_event(
        tenant_id=user.tenant_id,
        code=data.code,
        name=data.name,
        venue=data.venue,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        location_notes=data.location_notes,
    )
    return PopupEventRead.model_validate(event)


@router.post(
    "/stalls",
    response_model=PopupStallRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def create_stall(
    data: PopupStallCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PopupStallRead:
    stall = await PopupService(db).create_stall(
        tenant_id=user.tenant_id,
        event_id=data.event_id,
        stall_label=data.stall_label,
        operator_user_id=data.operator_user_id,
    )
    return PopupStallRead.model_validate(stall)


@router.get(
    "/events/{event_id}/stalls",
    response_model=list[PopupStallRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_stalls(
    event_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[PopupStallRead]:
    rows = await PopupService(db).list_stalls(
        tenant_id=user.tenant_id, event_id=event_id
    )
    return [PopupStallRead.model_validate(r) for r in rows]


@router.post(
    "/events/{event_id}/open",
    response_model=list[PopupInventorySnapshotRead],
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def open_event(
    event_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[PopupInventorySnapshotRead]:
    snapshots = await PopupService(db).open_event(
        tenant_id=user.tenant_id, event_id=event_id
    )
    return [PopupInventorySnapshotRead.model_validate(s) for s in snapshots]


@router.post(
    "/events/{event_id}/close",
    response_model=PopupCloseReport,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def close_event(
    event_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PopupCloseReport:
    report = await PopupService(db).close_event(
        tenant_id=user.tenant_id, event_id=event_id
    )
    lines = [
        PopupSoldLine(
            product_id=line.product_id,
            opening_stock=line.opening_stock,
            closing_stock=line.closing_stock,
            sold_count=line.sold_count,
        )
        for line in report
    ]
    return PopupCloseReport(
        event_id=event_id,
        lines=lines,
        total_sold_units=sum(line.sold_count for line in lines),
    )
