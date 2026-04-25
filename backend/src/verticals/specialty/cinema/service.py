from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.verticals.specialty.cinema.entity import Seat, SeatStatus, Show

DEFAULT_HOLD_SECONDS = 600  # 10 min — long enough for payment, short enough to avoid abuse


class CinemaService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Shows + seat map
    # ──────────────────────────────────────────────

    async def list_upcoming_shows(self, *, tenant_id: UUID) -> list[Show]:
        now = datetime.utcnow() - timedelta(minutes=15)
        stmt = (
            select(Show)
            .where(Show.tenant_id == tenant_id, Show.starts_at >= now)
            .order_by(Show.starts_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_seats(self, *, tenant_id: UUID, show_id: UUID) -> list[Seat]:
        await self._release_expired_holds(tenant_id=tenant_id, show_id=show_id)
        stmt = (
            select(Seat)
            .where(Seat.tenant_id == tenant_id, Seat.show_id == show_id)
            .order_by(Seat.label)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    @staticmethod
    def _rows_cols_labels(rows: int, cols: int) -> list[str]:
        """Generate A1..A<cols>, B1..B<cols> etc. for a conventional seat map."""
        labels: list[str] = []
        for r in range(rows):
            letter = chr(ord("A") + r)
            for c in range(1, cols + 1):
                labels.append(f"{letter}{c}")
        return labels

    async def create_show(
        self,
        *,
        tenant_id: UUID,
        title: str,
        screen: str,
        starts_at: datetime,
        ends_at: datetime,
        ticket_price_cents: int,
        seat_labels: list[str] | None = None,
        seat_map_rows: int | None = None,
        seat_map_cols: int | None = None,
    ) -> Show:
        show = Show(
            tenant_id=tenant_id,
            title=title,
            screen=screen,
            starts_at=starts_at,
            ends_at=ends_at,
            ticket_price_cents=ticket_price_cents,
        )
        self._session.add(show)
        await self._session.flush()

        labels = seat_labels or []
        if not labels and seat_map_rows and seat_map_cols:
            labels = self._rows_cols_labels(seat_map_rows, seat_map_cols)
        if not labels:
            raise ConflictError(
                "Provide either seat_labels or seat_map_rows+seat_map_cols."
            )

        self._session.add_all(
            [
                Seat(
                    tenant_id=tenant_id,
                    show_id=show.id,
                    label=label,
                    status=SeatStatus.AVAILABLE,
                    held_by=None,
                    held_until=None,
                    order_id=None,
                )
                for label in labels
            ]
        )
        await self._session.flush()
        return show

    # ──────────────────────────────────────────────
    # Holds + sale
    # ──────────────────────────────────────────────

    async def _release_expired_holds(
        self, *, tenant_id: UUID, show_id: UUID
    ) -> None:
        now = datetime.now(tz=UTC)
        stmt = select(Seat).where(
            Seat.tenant_id == tenant_id,
            Seat.show_id == show_id,
            Seat.status == SeatStatus.HELD,
            Seat.held_until.is_not(None),
            Seat.held_until < now,
        )
        for seat in (await self._session.execute(stmt)).scalars().all():
            seat.status = SeatStatus.AVAILABLE
            seat.held_by = None
            seat.held_until = None
        await self._session.flush()

    async def hold_seat(
        self,
        *,
        tenant_id: UUID,
        seat_id: UUID,
        held_by: str,
        ttl_seconds: int = DEFAULT_HOLD_SECONDS,
    ) -> Seat:
        seat = await self._session.get(Seat, seat_id)
        if seat is None or seat.tenant_id != tenant_id:
            raise NotFoundError("Seat not found.")
        now = datetime.now(tz=UTC)
        # Auto-release this specific seat if its hold lapsed
        if (
            seat.status == SeatStatus.HELD
            and seat.held_until is not None
            and seat.held_until < now
        ):
            seat.status = SeatStatus.AVAILABLE
            seat.held_by = None
            seat.held_until = None
        if seat.status == SeatStatus.HELD and seat.held_by != held_by:
            raise ConflictError("Seat is currently held by someone else.")
        if seat.status == SeatStatus.SOLD:
            raise ConflictError("Seat already sold.")
        seat.status = SeatStatus.HELD
        seat.held_by = held_by
        seat.held_until = now + timedelta(seconds=ttl_seconds)
        await self._session.flush()
        return seat

    async def release_seat(
        self, *, tenant_id: UUID, seat_id: UUID, held_by: str
    ) -> Seat:
        """Owner of a hold can release it early (e.g., they backed out of checkout)."""
        seat = await self._session.get(Seat, seat_id)
        if seat is None or seat.tenant_id != tenant_id:
            raise NotFoundError("Seat not found.")
        if seat.status != SeatStatus.HELD:
            return seat
        if seat.held_by != held_by:
            raise ConflictError("You don't own that hold.")
        seat.status = SeatStatus.AVAILABLE
        seat.held_by = None
        seat.held_until = None
        await self._session.flush()
        return seat

    async def sell_seat(
        self,
        *,
        tenant_id: UUID,
        seat_id: UUID,
        order_id: UUID | None = None,
        held_by: str | None = None,
    ) -> Seat:
        seat = await self._session.get(Seat, seat_id)
        if seat is None or seat.tenant_id != tenant_id:
            raise NotFoundError("Seat not found.")
        if seat.status == SeatStatus.SOLD:
            raise ConflictError("Seat already sold.")
        # If a hold exists, only the holder can convert it.
        if seat.status == SeatStatus.HELD and held_by is not None and seat.held_by != held_by:
            raise ConflictError("Seat is held by someone else.")
        seat.status = SeatStatus.SOLD
        seat.held_by = None
        seat.held_until = None
        seat.order_id = order_id
        await self._session.flush()
        return seat
