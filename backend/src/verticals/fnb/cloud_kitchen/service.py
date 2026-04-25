from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.verticals.fnb.cloud_kitchen.entity import (
    BrandOrder,
    BrandProduct,
    VirtualBrand,
)


class CloudKitchenService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Brands
    # ──────────────────────────────────────────────

    async def create_brand(
        self,
        *,
        tenant_id: UUID,
        code: str,
        name: str,
        logo_url: str | None = None,
        is_active: bool = True,
    ) -> VirtualBrand:
        stmt = select(VirtualBrand).where(
            VirtualBrand.tenant_id == tenant_id,
            VirtualBrand.code == code,
        )
        if (await self._session.execute(stmt)).scalar_one_or_none() is not None:
            raise ConflictError("A brand with this code already exists.")
        brand = VirtualBrand(
            tenant_id=tenant_id,
            code=code,
            name=name,
            logo_url=logo_url,
            is_active=is_active,
        )
        self._session.add(brand)
        await self._session.flush()
        return brand

    async def get_brand(self, *, tenant_id: UUID, brand_id: UUID) -> VirtualBrand:
        brand = await self._session.get(VirtualBrand, brand_id)
        if brand is None or brand.tenant_id != tenant_id:
            raise NotFoundError("Brand not found.")
        return brand

    async def list_brands(
        self, *, tenant_id: UUID, include_inactive: bool = False
    ) -> list[VirtualBrand]:
        stmt = select(VirtualBrand).where(VirtualBrand.tenant_id == tenant_id)
        if not include_inactive:
            stmt = stmt.where(VirtualBrand.is_active.is_(True))
        stmt = stmt.order_by(VirtualBrand.code)
        return list((await self._session.execute(stmt)).scalars().all())

    async def update_brand(
        self,
        *,
        tenant_id: UUID,
        brand_id: UUID,
        name: str | None = None,
        logo_url: str | None = None,
        is_active: bool | None = None,
    ) -> VirtualBrand:
        brand = await self.get_brand(tenant_id=tenant_id, brand_id=brand_id)
        if name is not None:
            brand.name = name
        if logo_url is not None:
            brand.logo_url = logo_url
        if is_active is not None:
            brand.is_active = is_active
        await self._session.flush()
        return brand

    # ──────────────────────────────────────────────
    # Brand ↔ product
    # ──────────────────────────────────────────────

    async def attach_product(
        self, *, tenant_id: UUID, brand_id: UUID, product_id: UUID
    ) -> BrandProduct:
        # Ensure the brand belongs to this tenant before we attach.
        await self.get_brand(tenant_id=tenant_id, brand_id=brand_id)
        stmt = select(BrandProduct).where(
            BrandProduct.brand_id == brand_id,
            BrandProduct.product_id == product_id,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            return existing
        assoc = BrandProduct(
            tenant_id=tenant_id,
            brand_id=brand_id,
            product_id=product_id,
        )
        self._session.add(assoc)
        await self._session.flush()
        return assoc

    async def detach_product(
        self, *, tenant_id: UUID, brand_id: UUID, product_id: UUID
    ) -> None:
        await self.get_brand(tenant_id=tenant_id, brand_id=brand_id)
        stmt = select(BrandProduct).where(
            BrandProduct.brand_id == brand_id,
            BrandProduct.product_id == product_id,
        )
        assoc = (await self._session.execute(stmt)).scalar_one_or_none()
        if assoc is None:
            raise NotFoundError("Product is not attached to this brand.")
        await self._session.delete(assoc)
        await self._session.flush()

    async def list_brand_products(
        self, *, tenant_id: UUID, brand_id: UUID
    ) -> list[BrandProduct]:
        await self.get_brand(tenant_id=tenant_id, brand_id=brand_id)
        stmt = (
            select(BrandProduct)
            .where(
                BrandProduct.tenant_id == tenant_id,
                BrandProduct.brand_id == brand_id,
            )
            .order_by(BrandProduct.created_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    # ──────────────────────────────────────────────
    # Orders audit
    # ──────────────────────────────────────────────

    async def record_brand_order(
        self,
        *,
        tenant_id: UUID,
        order_id: UUID,
        brand_id: UUID,
        external_order_ref: str | None = None,
    ) -> BrandOrder:
        """Tag which brand a completed sales order was for.

        Called after a sales checkout. Tenant-scoped unique on (tenant, order)
        so an order can only be assigned to one brand.
        """
        await self.get_brand(tenant_id=tenant_id, brand_id=brand_id)
        stmt = select(BrandOrder).where(
            BrandOrder.tenant_id == tenant_id,
            BrandOrder.order_id == order_id,
        )
        if (await self._session.execute(stmt)).scalar_one_or_none() is not None:
            raise ConflictError("This order is already tagged to a brand.")
        row = BrandOrder(
            tenant_id=tenant_id,
            order_id=order_id,
            brand_id=brand_id,
            external_order_ref=external_order_ref,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def list_brand_orders(
        self, *, tenant_id: UUID, brand_id: UUID
    ) -> list[BrandOrder]:
        await self.get_brand(tenant_id=tenant_id, brand_id=brand_id)
        stmt = (
            select(BrandOrder)
            .where(
                BrandOrder.tenant_id == tenant_id,
                BrandOrder.brand_id == brand_id,
            )
            .order_by(BrandOrder.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
