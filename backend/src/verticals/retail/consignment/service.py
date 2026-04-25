from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError, ValidationError
from src.verticals.retail.consignment.entity import (
    ConsignmentItem,
    ConsignmentItemStatus,
    Consignor,
    ConsignorPayout,
)


class ConsignmentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ── consignors ────────────────────────────────────────────────

    async def create_consignor(
        self,
        *,
        tenant_id: UUID,
        name: str,
        email: str | None = None,
        phone: str | None = None,
        payout_rate_pct: float = 50.0,
    ) -> Consignor:
        consignor = Consignor(
            tenant_id=tenant_id,
            name=name,
            email=email,
            phone=phone,
            payout_rate_pct=payout_rate_pct,
            balance_cents=0,
        )
        self._session.add(consignor)
        await self._session.flush()
        return consignor

    async def list_consignors(self, *, tenant_id: UUID) -> list[Consignor]:
        stmt = (
            select(Consignor)
            .where(Consignor.tenant_id == tenant_id)
            .order_by(Consignor.name)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def _get_consignor(
        self, *, tenant_id: UUID, consignor_id: UUID
    ) -> Consignor:
        consignor = await self._session.get(Consignor, consignor_id)
        if consignor is None or consignor.tenant_id != tenant_id:
            raise NotFoundError("Consignor not found.")
        return consignor

    # ── items ─────────────────────────────────────────────────────

    async def add_item(
        self,
        *,
        tenant_id: UUID,
        consignor_id: UUID,
        product_id: UUID,
        listed_price_cents: int,
    ) -> ConsignmentItem:
        # Validate the consignor exists under this tenant.
        await self._get_consignor(tenant_id=tenant_id, consignor_id=consignor_id)
        item = ConsignmentItem(
            tenant_id=tenant_id,
            consignor_id=consignor_id,
            product_id=product_id,
            status=ConsignmentItemStatus.LISTED,
            listed_price_cents=listed_price_cents,
            sold_at=None,
            sold_price_cents=None,
            consignor_share_cents=None,
            sold_order_id=None,
        )
        self._session.add(item)
        await self._session.flush()
        return item

    async def list_items(
        self,
        *,
        tenant_id: UUID,
        consignor_id: UUID | None = None,
        status: ConsignmentItemStatus | None = None,
    ) -> list[ConsignmentItem]:
        stmt = select(ConsignmentItem).where(ConsignmentItem.tenant_id == tenant_id)
        if consignor_id is not None:
            stmt = stmt.where(ConsignmentItem.consignor_id == consignor_id)
        if status is not None:
            stmt = stmt.where(ConsignmentItem.status == status)
        stmt = stmt.order_by(ConsignmentItem.listed_at.desc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def mark_sold(
        self,
        *,
        tenant_id: UUID,
        item_id: UUID,
        sold_price_cents: int,
        order_id: UUID,
    ) -> ConsignmentItem:
        item = await self._session.get(ConsignmentItem, item_id)
        if item is None or item.tenant_id != tenant_id:
            raise NotFoundError("Consignment item not found.")
        if item.status != ConsignmentItemStatus.LISTED:
            raise ConflictError("Only listed items can be marked sold.")
        consignor = await self._get_consignor(
            tenant_id=tenant_id, consignor_id=item.consignor_id
        )
        # Freeze the consignor's share using the rate *at sale time*. Using
        # integer math keeps cents exact — no float dust.
        share = (sold_price_cents * int(float(consignor.payout_rate_pct) * 100)) // 10000
        item.status = ConsignmentItemStatus.SOLD
        item.sold_at = datetime.now(timezone.utc)
        item.sold_price_cents = sold_price_cents
        item.consignor_share_cents = share
        item.sold_order_id = order_id
        consignor.balance_cents = consignor.balance_cents + share
        await self._session.flush()
        return item

    async def mark_returned(
        self, *, tenant_id: UUID, item_id: UUID
    ) -> ConsignmentItem:
        item = await self._session.get(ConsignmentItem, item_id)
        if item is None or item.tenant_id != tenant_id:
            raise NotFoundError("Consignment item not found.")
        if item.status != ConsignmentItemStatus.LISTED:
            raise ConflictError("Only listed items can be returned.")
        item.status = ConsignmentItemStatus.RETURNED
        await self._session.flush()
        return item

    # ── payouts ───────────────────────────────────────────────────

    async def pay_out(
        self,
        *,
        tenant_id: UUID,
        consignor_id: UUID,
        amount_cents: int,
        note: str | None = None,
    ) -> ConsignorPayout:
        if amount_cents <= 0:
            raise ValidationError("Payout amount must be positive.")
        consignor = await self._get_consignor(
            tenant_id=tenant_id, consignor_id=consignor_id
        )
        if amount_cents > consignor.balance_cents:
            raise ValidationError(
                "Payout exceeds the consignor's outstanding balance."
            )
        consignor.balance_cents = consignor.balance_cents - amount_cents
        payout = ConsignorPayout(
            tenant_id=tenant_id,
            consignor_id=consignor_id,
            amount_cents=amount_cents,
            balance_after_cents=consignor.balance_cents,
            note=note,
        )
        self._session.add(payout)
        await self._session.flush()
        return payout

    async def list_payouts(
        self, *, tenant_id: UUID, consignor_id: UUID
    ) -> list[ConsignorPayout]:
        stmt = (
            select(ConsignorPayout)
            .where(
                ConsignorPayout.tenant_id == tenant_id,
                ConsignorPayout.consignor_id == consignor_id,
            )
            .order_by(ConsignorPayout.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
