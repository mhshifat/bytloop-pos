from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.specialty.cinema.schemas import (
    HoldSeatRequest,
    ReleaseSeatRequest,
    SeatRead,
    SellSeatRequest,
    ShowCreate,
    ShowRead,
)
from src.verticals.specialty.cinema.service import CinemaService

router = APIRouter(prefix="/cinema", tags=["cinema"])


@router.post(
    "/shows",
    response_model=ShowRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def create_show(
    data: ShowCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ShowRead:
    show = await CinemaService(db).create_show(
        tenant_id=user.tenant_id,
        title=data.title,
        screen=data.screen,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        ticket_price_cents=data.ticket_price_cents,
        seat_labels=list(data.seat_labels) if data.seat_labels else None,
        seat_map_rows=data.seat_map_rows,
        seat_map_cols=data.seat_map_cols,
    )
    return ShowRead.model_validate(show)


@router.get(
    "/shows",
    response_model=list[ShowRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_shows(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[ShowRead]:
    rows = await CinemaService(db).list_upcoming_shows(tenant_id=user.tenant_id)
    return [ShowRead.model_validate(r) for r in rows]


@router.get(
    "/shows/{show_id}/seats",
    response_model=list[SeatRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_seats(
    show_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[SeatRead]:
    rows = await CinemaService(db).list_seats(
        tenant_id=user.tenant_id, show_id=show_id
    )
    return [SeatRead.model_validate(r) for r in rows]


@router.post(
    "/seats/{seat_id}/hold",
    response_model=SeatRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def hold_seat(
    seat_id: UUID,
    data: HoldSeatRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SeatRead:
    seat = await CinemaService(db).hold_seat(
        tenant_id=user.tenant_id,
        seat_id=seat_id,
        held_by=data.held_by,
        ttl_seconds=data.ttl_seconds,
    )
    return SeatRead.model_validate(seat)


@router.post(
    "/seats/{seat_id}/release",
    response_model=SeatRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def release_seat(
    seat_id: UUID,
    data: ReleaseSeatRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SeatRead:
    seat = await CinemaService(db).release_seat(
        tenant_id=user.tenant_id, seat_id=seat_id, held_by=data.held_by
    )
    return SeatRead.model_validate(seat)


@router.post(
    "/seats/{seat_id}/sell",
    response_model=SeatRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def sell_seat(
    seat_id: UUID,
    data: SellSeatRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> SeatRead:
    seat = await CinemaService(db).sell_seat(
        tenant_id=user.tenant_id,
        seat_id=seat_id,
        order_id=data.order_id,
        held_by=data.held_by,
    )
    return SeatRead.model_validate(seat)
