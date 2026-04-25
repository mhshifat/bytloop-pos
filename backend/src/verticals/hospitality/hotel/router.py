from __future__ import annotations

from datetime import date as _date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.hospitality.hotel.schemas import (
    FolioChargeCreate,
    FolioChargeRead,
    FolioRead,
    ReservationCreate,
    ReservationRead,
    RoomCreate,
    RoomRead,
    UpdateReservationStatusRequest,
)
from src.verticals.hospitality.hotel.service import HotelService

router = APIRouter(prefix="/hotel", tags=["hotel"])


@router.get(
    "/rooms",
    response_model=list[RoomRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_rooms(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[RoomRead]:
    rows = await HotelService(db).list_rooms(tenant_id=user.tenant_id)
    return [RoomRead.model_validate(r) for r in rows]


@router.post(
    "/rooms",
    response_model=RoomRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def add_room(
    data: RoomCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> RoomRead:
    room = await HotelService(db).add_room(
        tenant_id=user.tenant_id,
        number=data.number,
        category=data.category,
        nightly_rate_cents=data.nightly_rate_cents,
    )
    return RoomRead.model_validate(room)


@router.get(
    "/reservations",
    response_model=list[ReservationRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_reservations(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[ReservationRead]:
    rows = await HotelService(db).list_reservations(tenant_id=user.tenant_id)
    return [ReservationRead.model_validate(r) for r in rows]


@router.post(
    "/reservations",
    response_model=ReservationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def reserve(
    data: ReservationCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ReservationRead:
    reservation = await HotelService(db).reserve(
        tenant_id=user.tenant_id,
        room_id=data.room_id,
        customer_id=data.customer_id,
        check_in=data.check_in,
        check_out=data.check_out,
    )
    return ReservationRead.model_validate(reservation)


@router.patch(
    "/reservations/{reservation_id}/status",
    response_model=ReservationRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def update_reservation(
    reservation_id: UUID,
    data: UpdateReservationStatusRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ReservationRead:
    reservation = await HotelService(db).update_reservation_status(
        tenant_id=user.tenant_id, reservation_id=reservation_id, status=data.status
    )
    return ReservationRead.model_validate(reservation)


@router.get(
    "/rooms/available",
    response_model=list[RoomRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def available_rooms(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    check_in: _date = Query(..., alias="checkIn"),
    check_out: _date = Query(..., alias="checkOut"),
) -> list[RoomRead]:
    rows = await HotelService(db).available_rooms(
        tenant_id=user.tenant_id, check_in=check_in, check_out=check_out
    )
    return [RoomRead.model_validate(r) for r in rows]


@router.post(
    "/reservations/{reservation_id}/check-in",
    response_model=ReservationRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def check_in(
    reservation_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ReservationRead:
    reservation = await HotelService(db).check_in(
        tenant_id=user.tenant_id, reservation_id=reservation_id
    )
    return ReservationRead.model_validate(reservation)


@router.post(
    "/reservations/{reservation_id}/check-out",
    response_model=ReservationRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def check_out(
    reservation_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ReservationRead:
    reservation = await HotelService(db).check_out(
        tenant_id=user.tenant_id, reservation_id=reservation_id
    )
    return ReservationRead.model_validate(reservation)


@router.post(
    "/reservations/{reservation_id}/charges",
    response_model=FolioChargeRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def post_charge(
    reservation_id: UUID,
    data: FolioChargeCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> FolioChargeRead:
    charge = await HotelService(db).post_charge(
        tenant_id=user.tenant_id,
        reservation_id=reservation_id,
        description=data.description,
        amount_cents=data.amount_cents,
    )
    return FolioChargeRead.model_validate(charge)


@router.get(
    "/reservations/{reservation_id}/folio",
    response_model=FolioRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def folio(
    reservation_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> FolioRead:
    _resv, charges, nights, room_total, incidentals, total = await HotelService(
        db
    ).folio(tenant_id=user.tenant_id, reservation_id=reservation_id)
    return FolioRead(
        reservation_id=reservation_id,
        nights=nights,
        room_total_cents=room_total,
        incidentals_cents=incidentals,
        total_cents=total,
        charges=[FolioChargeRead.model_validate(c) for c in charges],
    )
