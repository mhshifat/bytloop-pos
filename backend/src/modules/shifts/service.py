from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.modules.inventory.api import InventoryService
from src.modules.shifts.entity import Shift, ShiftStatus
from src.modules.shifts.repository import ShiftRepository


class ShiftService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        inventory: InventoryService | None = None,
        shifts: ShiftRepository | None = None,
    ) -> None:
        self._session = session
        self._inventory = inventory or InventoryService(session)
        self._shifts = shifts or ShiftRepository(session)

    async def open(
        self, *, tenant_id: UUID, cashier_id: UUID, opening_float_cents: int
    ) -> Shift:
        existing = await self._shifts.open_for_cashier(
            tenant_id=tenant_id, cashier_id=cashier_id
        )
        if existing is not None:
            raise ConflictError("You already have an open shift.")

        location_id = await self._inventory.default_location_id(tenant_id=tenant_id)
        shift = Shift(
            tenant_id=tenant_id,
            location_id=location_id,
            cashier_id=cashier_id,
            status=ShiftStatus.OPEN,
            opening_float_cents=opening_float_cents,
        )
        return await self._shifts.add(shift)

    async def close(
        self, *, tenant_id: UUID, cashier_id: UUID, closing_counted_cents: int
    ) -> Shift:
        shift = await self._shifts.open_for_cashier(
            tenant_id=tenant_id, cashier_id=cashier_id
        )
        if shift is None:
            raise NotFoundError("No open shift.")

        cash_collected = await self._shifts.cash_total_since(
            tenant_id=tenant_id, since=shift.opened_at, cashier_id=cashier_id
        )
        expected = shift.opening_float_cents + cash_collected

        shift.status = ShiftStatus.CLOSED
        shift.closed_at = datetime.now(tz=UTC)
        shift.closing_counted_cents = closing_counted_cents
        shift.expected_cash_cents = expected
        shift.variance_cents = closing_counted_cents - expected
        await self._session.flush()
        return shift

    async def current(self, *, tenant_id: UUID, cashier_id: UUID) -> Shift | None:
        return await self._shifts.open_for_cashier(
            tenant_id=tenant_id, cashier_id=cashier_id
        )
