from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.catalog.entity import Category, Product


class ProductRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self,
        *,
        tenant_id: UUID,
        search: str | None = None,
        category_id: UUID | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[Product], bool]:
        """Return (rows, has_more). No COUNT(*) on a hot list — docs/PLAN.md §15b."""
        stmt = select(Product).where(Product.tenant_id == tenant_id).order_by(Product.name)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(func.lower(Product.name).like(like))
        if category_id:
            stmt = stmt.where(Product.category_id == category_id)
        stmt = stmt.limit(limit + 1).offset(offset)

        rows = (await self._session.execute(stmt)).scalars().all()
        has_more = len(rows) > limit
        return list(rows[:limit]), has_more

    async def get(self, product_id: UUID, *, tenant_id: UUID) -> Product | None:
        stmt = select(Product).where(Product.id == product_id, Product.tenant_id == tenant_id)
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_by_barcode(self, barcode: str, *, tenant_id: UUID) -> Product | None:
        stmt = select(Product).where(
            Product.barcode == barcode, Product.tenant_id == tenant_id
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def add(self, product: Product) -> Product:
        self._session.add(product)
        await self._session.flush()
        return product

    async def delete(self, product: Product) -> None:
        await self._session.delete(product)
        await self._session.flush()


class CategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(self, *, tenant_id: UUID) -> list[Category]:
        stmt = (
            select(Category).where(Category.tenant_id == tenant_id).order_by(Category.name)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def by_slug(self, *, tenant_id: UUID, slug: str) -> Category | None:
        stmt = select(Category).where(
            Category.tenant_id == tenant_id, Category.slug == slug.lower()
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def add(self, category: Category) -> Category:
        self._session.add(category)
        await self._session.flush()
        return category
