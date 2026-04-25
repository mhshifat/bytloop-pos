from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.verticals.retail.apparel.entity import ApparelVariant


class ApparelService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_for_product(self, *, tenant_id: UUID, product_id: UUID) -> list[ApparelVariant]:
        stmt = (
            select(ApparelVariant)
            .where(
                ApparelVariant.tenant_id == tenant_id,
                ApparelVariant.product_id == product_id,
            )
            .order_by(ApparelVariant.size, ApparelVariant.color)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def find_by_barcode(
        self, *, tenant_id: UUID, barcode: str
    ) -> ApparelVariant | None:
        """Resolve a scanned barcode to a specific (size, color) variant.

        Falls back to None so the caller can try other barcode tables
        (PLU, generic product.barcode) before 404-ing.
        """
        stmt = select(ApparelVariant).where(
            ApparelVariant.tenant_id == tenant_id,
            ApparelVariant.barcode == barcode,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def find_by_sku(
        self, *, tenant_id: UUID, sku: str
    ) -> ApparelVariant | None:
        stmt = select(ApparelVariant).where(
            ApparelVariant.tenant_id == tenant_id,
            ApparelVariant.sku == sku,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def update_variant(
        self,
        *,
        tenant_id: UUID,
        variant_id: UUID,
        barcode: str | None = None,
        gender: str | None = None,
        fit: str | None = None,
        material: str | None = None,
        price_cents_override: int | None = None,
    ) -> ApparelVariant:
        variant = await self._session.get(ApparelVariant, variant_id)
        if variant is None or variant.tenant_id != tenant_id:
            raise NotFoundError("Variant not found.")
        if barcode is not None:
            variant.barcode = barcode or None
        if gender is not None:
            variant.gender = gender or None
        if fit is not None:
            variant.fit = fit or None
        if material is not None:
            variant.material = material or None
        if price_cents_override is not None:
            variant.price_cents_override = (
                price_cents_override if price_cents_override >= 0 else None
            )
        await self._session.flush()
        return variant

    async def adjust_variant_stock(
        self, *, tenant_id: UUID, variant_id: UUID, delta: int
    ) -> ApparelVariant:
        """Direct delta on variant stock. Parent ``Product.track_inventory``
        stays authoritative for the parent catalog row; this is per-variant
        depth so a size-M isn't blocked because size-L is out.
        """
        variant = await self._session.get(ApparelVariant, variant_id)
        if variant is None or variant.tenant_id != tenant_id:
            raise NotFoundError("Variant not found.")
        new_qty = variant.stock_quantity + delta
        if new_qty < 0:
            raise ConflictError("Variant stock would go negative.")
        variant.stock_quantity = new_qty
        await self._session.flush()
        return variant

    async def bulk_create(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        sizes: list[str],
        colors: list[str],
        sku_prefix: str,
    ) -> list[ApparelVariant]:
        variants: list[ApparelVariant] = []
        for size in sizes:
            for color in colors:
                variants.append(
                    ApparelVariant(
                        tenant_id=tenant_id,
                        product_id=product_id,
                        sku=f"{sku_prefix}-{size}-{color}".upper(),
                        barcode=None,
                        size=size,
                        color=color,
                        gender=None,
                        fit=None,
                        material=None,
                        price_cents_override=None,
                        stock_quantity=0,
                    )
                )
        self._session.add_all(variants)
        await self._session.flush()
        return variants
