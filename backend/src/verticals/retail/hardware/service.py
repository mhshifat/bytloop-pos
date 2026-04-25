from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError, ValidationError
from src.modules.catalog.api import Product
from src.verticals.retail.hardware.entity import QuantityBreak


class HardwareService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def set_breaks(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        tiers: Sequence[tuple[int, int]],
    ) -> list[QuantityBreak]:
        """Atomically replace the ladder for a product.

        Every call wipes the existing rungs and inserts the new ones inside a
        single transaction (the enclosing request session commits on success,
        rolls back on any failure). Duplicate ``min_quantity`` values are
        rejected up-front so we surface a clean ``ValidationError`` rather
        than an IntegrityError from the unique constraint.
        """
        seen_mins: set[int] = set()
        for min_qty, price in tiers:
            if min_qty < 1:
                raise ValidationError("min_quantity must be 1 or greater.")
            if price < 0:
                raise ValidationError("unit_price_cents must not be negative.")
            if min_qty in seen_mins:
                raise ValidationError(
                    "Duplicate min_quantity in tier list — each threshold must be unique."
                )
            seen_mins.add(min_qty)

        # Verify the product exists under this tenant before mutating.
        product = await self._session.get(Product, product_id)
        if product is None or product.tenant_id != tenant_id:
            raise NotFoundError("Product not found.")

        await self._session.execute(
            delete(QuantityBreak).where(
                QuantityBreak.tenant_id == tenant_id,
                QuantityBreak.product_id == product_id,
            )
        )

        inserted: list[QuantityBreak] = []
        for min_qty, price in sorted(tiers, key=lambda t: t[0]):
            row = QuantityBreak(
                tenant_id=tenant_id,
                product_id=product_id,
                min_quantity=min_qty,
                unit_price_cents=price,
            )
            self._session.add(row)
            inserted.append(row)
        await self._session.flush()
        return inserted

    async def list_for_product(
        self, *, tenant_id: UUID, product_id: UUID
    ) -> list[QuantityBreak]:
        stmt = (
            select(QuantityBreak)
            .where(
                QuantityBreak.tenant_id == tenant_id,
                QuantityBreak.product_id == product_id,
            )
            .order_by(QuantityBreak.min_quantity.asc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def resolve_unit_price(
        self, *, tenant_id: UUID, product_id: UUID, quantity: int
    ) -> tuple[int, int | None]:
        """Return ``(unit_price_cents, matched_min_quantity)``.

        Picks the tier with the greatest ``min_quantity <= quantity``. If the
        cart's quantity is below every tier's threshold, fall back to the
        product's base ``price_cents`` and return ``matched_min_quantity=None``.
        """
        if quantity < 1:
            raise ValidationError("quantity must be 1 or greater.")

        stmt = (
            select(QuantityBreak)
            .where(
                QuantityBreak.tenant_id == tenant_id,
                QuantityBreak.product_id == product_id,
                QuantityBreak.min_quantity <= quantity,
            )
            .order_by(QuantityBreak.min_quantity.desc())
            .limit(1)
        )
        best = (await self._session.execute(stmt)).scalar_one_or_none()
        if best is not None:
            return best.unit_price_cents, best.min_quantity

        product = await self._session.get(Product, product_id)
        if product is None or product.tenant_id != tenant_id:
            raise NotFoundError("Product not found.")
        return product.price_cents, None
