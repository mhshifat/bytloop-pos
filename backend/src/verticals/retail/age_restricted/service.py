from __future__ import annotations

from collections.abc import Sequence
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ValidationError
from src.verticals.retail.age_restricted.entity import (
    AgeRestrictedProduct,
    AgeVerificationLog,
)


def _age_on(today: date, dob: date) -> int:
    """Whole-year age on ``today`` given ``dob`` — no floor-division surprises
    around leap days.
    """
    years = today.year - dob.year
    if (today.month, today.day) < (dob.month, dob.day):
        years -= 1
    return years


class AgeRestrictedService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def set_min_age(
        self, *, tenant_id: UUID, product_id: UUID, min_age_years: int
    ) -> AgeRestrictedProduct:
        existing = await self._session.get(AgeRestrictedProduct, product_id)
        if existing is not None and existing.tenant_id == tenant_id:
            existing.min_age_years = min_age_years
            await self._session.flush()
            return existing
        row = AgeRestrictedProduct(
            product_id=product_id,
            tenant_id=tenant_id,
            min_age_years=min_age_years,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def requires_verification(
        self, *, tenant_id: UUID, product_ids: Sequence[UUID]
    ) -> list[dict]:
        """Return the subset of ``product_ids`` that have an age rule.

        Each entry is ``{"product_id": UUID, "min_age_years": int}`` — the
        cashier UI uses this to decide whether to pop the DOB prompt.
        """
        if not product_ids:
            return []
        stmt = select(AgeRestrictedProduct).where(
            AgeRestrictedProduct.tenant_id == tenant_id,
            AgeRestrictedProduct.product_id.in_(list(product_ids)),
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [
            {"product_id": r.product_id, "min_age_years": r.min_age_years}
            for r in rows
        ]

    async def record_verification(
        self,
        *,
        tenant_id: UUID,
        order_id: UUID,
        customer_dob: date,
        verified_by_user_id: UUID,
        product_ids: Sequence[UUID] | None = None,
    ) -> AgeVerificationLog:
        """Log a verification after checking the DOB clears every product rule.

        ``product_ids`` is optional: when omitted, we look up every rule row
        for the tenant and use the strictest applicable one. In practice the
        caller should pass the cart's product ids so we only gate on what's
        actually being sold.
        """
        today = datetime.now(timezone.utc).date()
        age = _age_on(today, customer_dob)
        if age < 0:
            raise ValidationError("Date of birth cannot be in the future.")

        # Figure out the strictest min_age across the products in question.
        if product_ids:
            stmt = select(AgeRestrictedProduct).where(
                AgeRestrictedProduct.tenant_id == tenant_id,
                AgeRestrictedProduct.product_id.in_(list(product_ids)),
            )
        else:
            stmt = select(AgeRestrictedProduct).where(
                AgeRestrictedProduct.tenant_id == tenant_id,
            )
        rules = (await self._session.execute(stmt)).scalars().all()
        min_age_required = max((r.min_age_years for r in rules), default=0)

        if age < min_age_required:
            raise ValidationError(
                f"Customer is {age}; minimum age required is {min_age_required}."
            )

        log = AgeVerificationLog(
            tenant_id=tenant_id,
            order_id=order_id,
            verified_by_user_id=verified_by_user_id,
            customer_dob=customer_dob,
            min_age_required=min_age_required,
            verified_age_years=age,
        )
        self._session.add(log)
        await self._session.flush()
        return log
