from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError, ValidationError
from src.verticals.retail.furniture.entity import CustomOrder, CustomOrderStatus


# The legal forward edges of the workflow. Any other transition raises
# ConflictError. ``cancelled`` is terminal — a cancelled job is cancelled,
# even if the customer changes their mind (they can re-quote a new row).
_ALLOWED_TRANSITIONS: dict[CustomOrderStatus, frozenset[CustomOrderStatus]] = {
    CustomOrderStatus.QUOTED: frozenset(
        {CustomOrderStatus.IN_PRODUCTION, CustomOrderStatus.CANCELLED}
    ),
    CustomOrderStatus.IN_PRODUCTION: frozenset(
        {CustomOrderStatus.READY, CustomOrderStatus.CANCELLED}
    ),
    CustomOrderStatus.READY: frozenset(
        {CustomOrderStatus.DELIVERED, CustomOrderStatus.CANCELLED}
    ),
    CustomOrderStatus.DELIVERED: frozenset(),
    CustomOrderStatus.CANCELLED: frozenset(),
}


class FurnitureService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _get(self, *, tenant_id: UUID, order_id: UUID) -> CustomOrder:
        row = await self._session.get(CustomOrder, order_id)
        if row is None or row.tenant_id != tenant_id:
            raise NotFoundError("Custom order not found.")
        return row

    def _assert_transition(
        self, *, current: CustomOrderStatus, target: CustomOrderStatus
    ) -> None:
        if target not in _ALLOWED_TRANSITIONS[current]:
            raise ConflictError(
                f"Cannot move a {current.value} order to {target.value}."
            )

    # ── create / read ────────────────────────────────────────────────

    async def quote(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        description: str,
        quoted_price_cents: int,
        customer_id: UUID | None = None,
        dimensions_cm: str | None = None,
        material: str | None = None,
        finish: str | None = None,
        estimated_ready_on: date | None = None,
    ) -> CustomOrder:
        if quoted_price_cents < 0:
            raise ValidationError("Quoted price cannot be negative.")
        row = CustomOrder(
            tenant_id=tenant_id,
            product_id=product_id,
            description=description,
            quoted_price_cents=quoted_price_cents,
            customer_id=customer_id,
            dimensions_cm=dimensions_cm,
            material=material,
            finish=finish,
            status=CustomOrderStatus.QUOTED,
            estimated_ready_on=estimated_ready_on,
            order_id=None,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def update_quote(
        self,
        *,
        tenant_id: UUID,
        order_id: UUID,
        description: str | None = None,
        quoted_price_cents: int | None = None,
        dimensions_cm: str | None = None,
        material: str | None = None,
        finish: str | None = None,
        estimated_ready_on: date | None = None,
    ) -> CustomOrder:
        row = await self._get(tenant_id=tenant_id, order_id=order_id)
        # Edits only make sense while still quoting — once production starts
        # the workshop shouldn't be chasing a moving target.
        if row.status != CustomOrderStatus.QUOTED:
            raise ConflictError("Only quoted orders can be edited.")
        if description is not None:
            row.description = description
        if quoted_price_cents is not None:
            if quoted_price_cents < 0:
                raise ValidationError("Quoted price cannot be negative.")
            row.quoted_price_cents = quoted_price_cents
        if dimensions_cm is not None:
            row.dimensions_cm = dimensions_cm
        if material is not None:
            row.material = material
        if finish is not None:
            row.finish = finish
        if estimated_ready_on is not None:
            row.estimated_ready_on = estimated_ready_on
        await self._session.flush()
        return row

    async def get(self, *, tenant_id: UUID, order_id: UUID) -> CustomOrder:
        return await self._get(tenant_id=tenant_id, order_id=order_id)

    async def list_for_customer(
        self, *, tenant_id: UUID, customer_id: UUID
    ) -> list[CustomOrder]:
        stmt = (
            select(CustomOrder)
            .where(
                CustomOrder.tenant_id == tenant_id,
                CustomOrder.customer_id == customer_id,
            )
            .order_by(CustomOrder.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_by_status(
        self, *, tenant_id: UUID, status: CustomOrderStatus
    ) -> list[CustomOrder]:
        stmt = (
            select(CustomOrder)
            .where(
                CustomOrder.tenant_id == tenant_id,
                CustomOrder.status == status,
            )
            .order_by(CustomOrder.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    # ── status transitions ───────────────────────────────────────────

    async def start_production(
        self,
        *,
        tenant_id: UUID,
        order_id: UUID,
        estimated_ready_on: date | None = None,
    ) -> CustomOrder:
        row = await self._get(tenant_id=tenant_id, order_id=order_id)
        self._assert_transition(
            current=row.status, target=CustomOrderStatus.IN_PRODUCTION
        )
        row.status = CustomOrderStatus.IN_PRODUCTION
        if estimated_ready_on is not None:
            row.estimated_ready_on = estimated_ready_on
        await self._session.flush()
        return row

    async def mark_ready(
        self, *, tenant_id: UUID, order_id: UUID
    ) -> CustomOrder:
        row = await self._get(tenant_id=tenant_id, order_id=order_id)
        self._assert_transition(current=row.status, target=CustomOrderStatus.READY)
        row.status = CustomOrderStatus.READY
        await self._session.flush()
        return row

    async def mark_delivered(
        self,
        *,
        tenant_id: UUID,
        order_id: UUID,
        paid_order_id: UUID | None = None,
    ) -> CustomOrder:
        row = await self._get(tenant_id=tenant_id, order_id=order_id)
        self._assert_transition(
            current=row.status, target=CustomOrderStatus.DELIVERED
        )
        row.status = CustomOrderStatus.DELIVERED
        if paid_order_id is not None:
            row.order_id = paid_order_id
        await self._session.flush()
        return row

    async def cancel(
        self, *, tenant_id: UUID, order_id: UUID
    ) -> CustomOrder:
        row = await self._get(tenant_id=tenant_id, order_id=order_id)
        self._assert_transition(
            current=row.status, target=CustomOrderStatus.CANCELLED
        )
        row.status = CustomOrderStatus.CANCELLED
        await self._session.flush()
        return row
