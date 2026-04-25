from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.modules.sales.api import OrderType, PaymentMethod, SalesService
from src.modules.sales.schemas import CartItemInput
from src.verticals.fnb.preorders.entity import Preorder, PreorderItem, PreorderStatus
from src.verticals.fnb.preorders.schemas import PreorderItemInput


class PreorderService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        sales: SalesService | None = None,
    ) -> None:
        self._session = session
        self._sales = sales or SalesService(session)

    async def create(
        self,
        *,
        tenant_id: UUID,
        customer_id: UUID | None,
        pickup_at: datetime,
        notes: str | None,
        items: list[PreorderItemInput],
    ) -> Preorder:
        total = sum(i.unit_price_cents * i.quantity for i in items)
        preorder = Preorder(
            tenant_id=tenant_id,
            customer_id=customer_id,
            pickup_at=pickup_at,
            status=PreorderStatus.PENDING,
            order_id=None,
            notes=notes,
            total_cents=total,
        )
        self._session.add(preorder)
        await self._session.flush()

        self._session.add_all(
            [
                PreorderItem(
                    tenant_id=tenant_id,
                    preorder_id=preorder.id,
                    product_id=i.product_id,
                    quantity=i.quantity,
                    unit_price_cents=i.unit_price_cents,
                )
                for i in items
            ]
        )
        await self._session.flush()
        return preorder

    async def get(self, *, tenant_id: UUID, preorder_id: UUID) -> Preorder:
        preorder = await self._session.get(Preorder, preorder_id)
        if preorder is None or preorder.tenant_id != tenant_id:
            raise NotFoundError("Preorder not found.")
        return preorder

    async def list_for_day(self, *, tenant_id: UUID, day: date) -> list[Preorder]:
        start = datetime.combine(day, time.min, tzinfo=UTC)
        end = start + timedelta(days=1)
        stmt = (
            select(Preorder)
            .where(
                Preorder.tenant_id == tenant_id,
                Preorder.pickup_at >= start,
                Preorder.pickup_at < end,
            )
            .order_by(Preorder.pickup_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_upcoming(self, *, tenant_id: UUID, days: int = 7) -> list[Preorder]:
        now = datetime.now(tz=UTC)
        end = now + timedelta(days=days)
        stmt = (
            select(Preorder)
            .where(
                Preorder.tenant_id == tenant_id,
                Preorder.pickup_at >= now,
                Preorder.pickup_at < end,
                Preorder.status.in_(
                    [
                        PreorderStatus.PENDING,
                        PreorderStatus.PREPARING,
                        PreorderStatus.READY,
                    ]
                ),
            )
            .order_by(Preorder.pickup_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def update_status(
        self, *, tenant_id: UUID, preorder_id: UUID, status: PreorderStatus
    ) -> Preorder:
        preorder = await self.get(tenant_id=tenant_id, preorder_id=preorder_id)
        preorder.status = status
        await self._session.flush()
        return preorder

    async def list_items(
        self, *, tenant_id: UUID, preorder_id: UUID
    ) -> list[PreorderItem]:
        stmt = (
            select(PreorderItem)
            .where(
                PreorderItem.tenant_id == tenant_id,
                PreorderItem.preorder_id == preorder_id,
            )
            .order_by(PreorderItem.id)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def convert_to_order(
        self,
        *,
        tenant_id: UUID,
        cashier_id: UUID,
        preorder_id: UUID,
        payment_method: PaymentMethod = PaymentMethod.CASH,
        amount_tendered_cents: int | None = None,
        payment_reference: str | None = None,
    ) -> Preorder:
        """Settle a preorder through the sales.api checkout and link back."""
        preorder = await self.get(tenant_id=tenant_id, preorder_id=preorder_id)
        if preorder.status == PreorderStatus.PICKED_UP:
            raise ConflictError("Preorder already picked up.")
        if preorder.status == PreorderStatus.CANCELLED:
            raise ConflictError("Cancelled preorders can't be converted.")
        if preorder.order_id is not None:
            raise ConflictError("Preorder already linked to an order.")

        items = await self.list_items(tenant_id=tenant_id, preorder_id=preorder_id)
        if not items:
            raise ConflictError("Preorder has no items to convert.")

        cart = [
            CartItemInput(product_id=i.product_id, quantity=i.quantity)
            for i in items
        ]
        sale = await self._sales.checkout(
            tenant_id=tenant_id,
            cashier_id=cashier_id,
            items=cart,
            order_type=OrderType.TAKEAWAY,
            payment_method=payment_method,
            amount_tendered_cents=amount_tendered_cents,
            customer_id=preorder.customer_id,
            payment_reference=payment_reference,
        )
        preorder.order_id = sale.order.id
        preorder.status = PreorderStatus.PICKED_UP
        await self._session.flush()
        return preorder
