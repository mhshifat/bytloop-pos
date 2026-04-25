from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.modules.sales.api import OrderType, PaymentMethod, SalesService
from src.modules.sales.schemas import CartItemInput
from src.verticals.fnb.bar_tabs.entity import BarTab, BarTabLine, BarTabStatus


class BarTabService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        sales: SalesService | None = None,
    ) -> None:
        self._session = session
        self._sales = sales or SalesService(session)

    # ──────────────────────────────────────────────
    # Tab lifecycle
    # ──────────────────────────────────────────────

    async def open_tab(
        self,
        *,
        tenant_id: UUID,
        opened_by_user_id: UUID,
        customer_id: UUID | None,
        preauth_reference: str | None,
    ) -> BarTab:
        tab = BarTab(
            tenant_id=tenant_id,
            customer_id=customer_id,
            opened_by_user_id=opened_by_user_id,
            status=BarTabStatus.OPEN,
            preauth_reference=preauth_reference,
            closed_at=None,
            order_id=None,
            total_cents=0,
        )
        self._session.add(tab)
        await self._session.flush()
        return tab

    async def get(self, *, tenant_id: UUID, tab_id: UUID) -> BarTab:
        tab = await self._session.get(BarTab, tab_id)
        if tab is None or tab.tenant_id != tenant_id:
            raise NotFoundError("Tab not found.")
        return tab

    async def list_open_tabs(self, *, tenant_id: UUID) -> list[BarTab]:
        stmt = (
            select(BarTab)
            .where(
                BarTab.tenant_id == tenant_id,
                BarTab.status == BarTabStatus.OPEN,
            )
            .order_by(BarTab.opened_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    # ──────────────────────────────────────────────
    # Lines
    # ──────────────────────────────────────────────

    async def add_line(
        self,
        *,
        tenant_id: UUID,
        tab_id: UUID,
        product_id: UUID,
        quantity: int,
        unit_price_cents: int,
    ) -> BarTabLine:
        tab = await self.get(tenant_id=tenant_id, tab_id=tab_id)
        if tab.status != BarTabStatus.OPEN:
            raise ConflictError("Tab is not open.")
        line = BarTabLine(
            tenant_id=tenant_id,
            tab_id=tab_id,
            product_id=product_id,
            quantity=quantity,
            unit_price_cents=unit_price_cents,
        )
        self._session.add(line)
        tab.total_cents += quantity * unit_price_cents
        await self._session.flush()
        return line

    async def list_lines(
        self, *, tenant_id: UUID, tab_id: UUID
    ) -> list[BarTabLine]:
        stmt = (
            select(BarTabLine)
            .where(
                BarTabLine.tenant_id == tenant_id,
                BarTabLine.tab_id == tab_id,
            )
            .order_by(BarTabLine.added_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    # ──────────────────────────────────────────────
    # Close — settles through sales.api
    # ──────────────────────────────────────────────

    async def close_tab(
        self,
        *,
        tenant_id: UUID,
        cashier_id: UUID,
        tab_id: UUID,
    ) -> BarTab:
        tab = await self.get(tenant_id=tenant_id, tab_id=tab_id)
        if tab.status != BarTabStatus.OPEN:
            raise ConflictError("Tab is not open.")
        lines = await self.list_lines(tenant_id=tenant_id, tab_id=tab_id)
        if not lines:
            raise ConflictError("Cannot close an empty tab — abandon it instead.")

        # Aggregate by product so the sales cart is as compact as possible.
        qty_by_product: dict[UUID, int] = {}
        for line in lines:
            qty_by_product[line.product_id] = (
                qty_by_product.get(line.product_id, 0) + line.quantity
            )
        cart = [
            CartItemInput(product_id=pid, quantity=qty)
            for pid, qty in qty_by_product.items()
        ]

        sale = await self._sales.checkout(
            tenant_id=tenant_id,
            cashier_id=cashier_id,
            items=cart,
            order_type=OrderType.DINE_IN,
            # Pre-auth implies card — use CARD as the public method and
            # pass the gateway handle through as the payment reference.
            payment_method=PaymentMethod.CARD,
            amount_tendered_cents=None,
            customer_id=tab.customer_id,
            payment_reference=tab.preauth_reference,
        )
        tab.status = BarTabStatus.CLOSED
        tab.closed_at = datetime.now(tz=UTC)
        tab.order_id = sale.order.id
        tab.total_cents = sale.order.total_cents
        await self._session.flush()
        return tab

    async def abandon_tab(self, *, tenant_id: UUID, tab_id: UUID) -> BarTab:
        tab = await self.get(tenant_id=tenant_id, tab_id=tab_id)
        if tab.status != BarTabStatus.OPEN:
            raise ConflictError("Only open tabs can be abandoned.")
        tab.status = BarTabStatus.ABANDONED
        tab.closed_at = datetime.now(tz=UTC)
        await self._session.flush()
        return tab
