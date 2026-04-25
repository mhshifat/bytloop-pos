from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError, ValidationError
from src.modules.customers.api import Customer
from src.verticals.fnb.cafe_loyalty.entity import LoyaltyCard


class CafeLoyaltyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def issue_card(
        self,
        *,
        tenant_id: UUID,
        customer_id: UUID,
        card_code: str,
        punches_required: int = 10,
    ) -> LoyaltyCard:
        if punches_required < 1:
            raise ValidationError("punches_required must be 1 or greater.")

        customer = await self._session.get(Customer, customer_id)
        if customer is None or customer.tenant_id != tenant_id:
            raise NotFoundError("Customer not found.")

        clash = (
            await self._session.execute(
                select(LoyaltyCard).where(
                    LoyaltyCard.tenant_id == tenant_id,
                    LoyaltyCard.card_code == card_code,
                )
            )
        ).scalar_one_or_none()
        if clash is not None:
            raise ConflictError("That card code is already in use.")

        card = LoyaltyCard(
            tenant_id=tenant_id,
            customer_id=customer_id,
            card_code=card_code,
            punches_required=punches_required,
        )
        self._session.add(card)
        await self._session.flush()
        return card

    async def _get_by_code(
        self, *, tenant_id: UUID, card_code: str
    ) -> LoyaltyCard:
        stmt = select(LoyaltyCard).where(
            LoyaltyCard.tenant_id == tenant_id,
            LoyaltyCard.card_code == card_code,
        )
        card = (await self._session.execute(stmt)).scalar_one_or_none()
        if card is None:
            raise NotFoundError("Loyalty card not found.")
        return card

    async def punch(
        self, *, tenant_id: UUID, card_code: str, count: int = 1
    ) -> tuple[LoyaltyCard, bool]:
        """Record ``count`` punches, rolling over every ``punches_required``.

        A bulk punch (``count > 1``) may cross the threshold more than once —
        e.g. a card at 9/10 that receives 15 punches earns two free items and
        ends at 4/10. ``earned_this_punch`` reports whether *any* free-item
        credit was added during this call.
        """
        if count < 1:
            raise ValidationError("count must be 1 or greater.")

        card = await self._get_by_code(tenant_id=tenant_id, card_code=card_code)

        # Accumulate, then pull out whole free-items with floor-division. This
        # naturally handles any ``count`` size without a loop and keeps the
        # two counters (current / lifetime) consistent.
        card.total_punches_lifetime += count
        combined = card.punches_current + count
        earned_now = combined // card.punches_required
        card.free_items_earned += earned_now
        card.punches_current = combined % card.punches_required
        await self._session.flush()
        return card, earned_now > 0

    async def redeem_free_item(
        self, *, tenant_id: UUID, card_code: str
    ) -> LoyaltyCard:
        card = await self._get_by_code(tenant_id=tenant_id, card_code=card_code)
        if card.free_items_earned <= 0:
            raise ConflictError("No free items available to redeem.")
        card.free_items_earned -= 1
        await self._session.flush()
        return card

    async def list_for_customer(
        self, *, tenant_id: UUID, customer_id: UUID
    ) -> list[LoyaltyCard]:
        stmt = (
            select(LoyaltyCard)
            .where(
                LoyaltyCard.tenant_id == tenant_id,
                LoyaltyCard.customer_id == customer_id,
            )
            .order_by(LoyaltyCard.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
