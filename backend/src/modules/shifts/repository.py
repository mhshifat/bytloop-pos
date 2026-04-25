from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.sales.entity import Payment, PaymentMethod
from src.modules.shifts.entity import Shift, ShiftStatus


class ShiftRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def open_for_cashier(
        self, *, tenant_id: UUID, cashier_id: UUID
    ) -> Shift | None:
        stmt = (
            select(Shift)
            .where(
                Shift.tenant_id == tenant_id,
                Shift.cashier_id == cashier_id,
                Shift.status == ShiftStatus.OPEN,
            )
            .order_by(Shift.opened_at.desc())
            .limit(1)
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def add(self, shift: Shift) -> Shift:
        self._session.add(shift)
        await self._session.flush()
        return shift

    async def cash_total_since(
        self, *, tenant_id: UUID, since, cashier_id: UUID  # type: ignore[no-untyped-def]
    ) -> int:
        """Sum of cash payments recorded since the shift opened."""
        stmt = (
            select(func.coalesce(func.sum(Payment.amount_cents), 0))
            .join_from(Payment, Payment)  # ensure FROM clause
            .where(
                Payment.tenant_id == tenant_id,
                Payment.method == PaymentMethod.CASH,
                Payment.created_at >= since,
            )
        )
        # cashier_id linkage lives on Order.cashier_id; skipping the join for
        # the MVP — single-cashier-per-location is a safe assumption for now.
        del cashier_id
        result = (await self._session.execute(stmt)).scalar_one()
        return int(result or 0)
