from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.verticals.hospitality.hotel.entity import (
    FolioCharge,
    Reservation,
    ReservationStatus,
    Room,
)


class HotelService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Rooms
    # ──────────────────────────────────────────────

    async def list_rooms(self, *, tenant_id: UUID) -> list[Room]:
        stmt = select(Room).where(Room.tenant_id == tenant_id).order_by(Room.number)
        return list((await self._session.execute(stmt)).scalars().all())

    async def add_room(
        self,
        *,
        tenant_id: UUID,
        number: str,
        category: str,
        nightly_rate_cents: int,
    ) -> Room:
        room = Room(
            tenant_id=tenant_id,
            number=number,
            category=category,
            nightly_rate_cents=nightly_rate_cents,
        )
        self._session.add(room)
        await self._session.flush()
        return room

    async def available_rooms(
        self, *, tenant_id: UUID, check_in: date, check_out: date
    ) -> list[Room]:
        """Rooms with no overlapping BOOKED/CHECKED_IN reservation in window."""
        if check_out <= check_in:
            raise ConflictError("Check-out must be after check-in.")
        booked_subq = (
            select(Reservation.room_id)
            .where(
                Reservation.tenant_id == tenant_id,
                Reservation.status.in_(
                    [ReservationStatus.BOOKED, ReservationStatus.CHECKED_IN]
                ),
                Reservation.check_in < check_out,
                Reservation.check_out > check_in,
            )
        )
        stmt = (
            select(Room)
            .where(
                Room.tenant_id == tenant_id,
                Room.id.notin_(booked_subq),
            )
            .order_by(Room.number)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    # ──────────────────────────────────────────────
    # Reservations
    # ──────────────────────────────────────────────

    async def list_reservations(self, *, tenant_id: UUID) -> list[Reservation]:
        stmt = (
            select(Reservation)
            .where(Reservation.tenant_id == tenant_id)
            .order_by(Reservation.check_in.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def reserve(
        self,
        *,
        tenant_id: UUID,
        room_id: UUID,
        customer_id: UUID,
        check_in: date,
        check_out: date,
    ) -> Reservation:
        if check_out <= check_in:
            raise ConflictError("Check-out must be after check-in.")
        clash_stmt = select(Reservation).where(
            Reservation.tenant_id == tenant_id,
            Reservation.room_id == room_id,
            Reservation.status.in_(
                [ReservationStatus.BOOKED, ReservationStatus.CHECKED_IN]
            ),
            or_(
                and_(Reservation.check_in <= check_in, Reservation.check_out > check_in),
                and_(Reservation.check_in < check_out, Reservation.check_out >= check_out),
                and_(Reservation.check_in >= check_in, Reservation.check_out <= check_out),
            ),
        )
        clash = (await self._session.execute(clash_stmt)).scalar_one_or_none()
        if clash is not None:
            raise ConflictError("Room is already booked for those dates.")

        reservation = Reservation(
            tenant_id=tenant_id,
            room_id=room_id,
            customer_id=customer_id,
            status=ReservationStatus.BOOKED,
            check_in=check_in,
            check_out=check_out,
            checked_in_at=None,
            checked_out_at=None,
        )
        self._session.add(reservation)
        await self._session.flush()
        return reservation

    async def update_reservation_status(
        self, *, tenant_id: UUID, reservation_id: UUID, status: ReservationStatus
    ) -> Reservation:
        reservation = await self._session.get(Reservation, reservation_id)
        if reservation is None or reservation.tenant_id != tenant_id:
            raise NotFoundError("Reservation not found.")
        reservation.status = status
        await self._session.flush()
        return reservation

    async def check_in(
        self, *, tenant_id: UUID, reservation_id: UUID
    ) -> Reservation:
        reservation = await self._session.get(Reservation, reservation_id)
        if reservation is None or reservation.tenant_id != tenant_id:
            raise NotFoundError("Reservation not found.")
        if reservation.status != ReservationStatus.BOOKED:
            raise ConflictError(
                f"Cannot check in a {reservation.status.value} reservation."
            )
        reservation.status = ReservationStatus.CHECKED_IN
        reservation.checked_in_at = datetime.now(tz=UTC)
        await self._session.flush()
        return reservation

    async def check_out(
        self, *, tenant_id: UUID, reservation_id: UUID
    ) -> Reservation:
        reservation = await self._session.get(Reservation, reservation_id)
        if reservation is None or reservation.tenant_id != tenant_id:
            raise NotFoundError("Reservation not found.")
        if reservation.status != ReservationStatus.CHECKED_IN:
            raise ConflictError(
                f"Cannot check out a {reservation.status.value} reservation."
            )
        reservation.status = ReservationStatus.CHECKED_OUT
        reservation.checked_out_at = datetime.now(tz=UTC)
        await self._session.flush()
        return reservation

    # ──────────────────────────────────────────────
    # Folio
    # ──────────────────────────────────────────────

    async def post_charge(
        self,
        *,
        tenant_id: UUID,
        reservation_id: UUID,
        description: str,
        amount_cents: int,
    ) -> FolioCharge:
        reservation = await self._session.get(Reservation, reservation_id)
        if reservation is None or reservation.tenant_id != tenant_id:
            raise NotFoundError("Reservation not found.")
        if reservation.status == ReservationStatus.CANCELLED:
            raise ConflictError("Can't post to a cancelled reservation.")
        charge = FolioCharge(
            tenant_id=tenant_id,
            reservation_id=reservation_id,
            description=description,
            amount_cents=amount_cents,
        )
        self._session.add(charge)
        await self._session.flush()
        return charge

    async def folio(
        self, *, tenant_id: UUID, reservation_id: UUID
    ) -> tuple[Reservation, list[FolioCharge], int, int, int, int]:
        """Return (reservation, charges, nights, room_total, incidentals, grand)."""
        reservation = await self._session.get(Reservation, reservation_id)
        if reservation is None or reservation.tenant_id != tenant_id:
            raise NotFoundError("Reservation not found.")
        room = await self._session.get(Room, reservation.room_id)
        if room is None:
            raise NotFoundError("Room not found.")

        stmt = (
            select(FolioCharge)
            .where(
                FolioCharge.tenant_id == tenant_id,
                FolioCharge.reservation_id == reservation_id,
            )
            .order_by(FolioCharge.posted_at)
        )
        charges = list((await self._session.execute(stmt)).scalars().all())
        nights = max(1, (reservation.check_out - reservation.check_in).days)
        room_total = nights * room.nightly_rate_cents
        incidentals = sum(c.amount_cents for c in charges)
        return (
            reservation,
            charges,
            nights,
            room_total,
            incidentals,
            room_total + incidentals,
        )
