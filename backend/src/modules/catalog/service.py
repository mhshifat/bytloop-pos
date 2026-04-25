from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.modules.audit.api import AuditService
from src.modules.catalog.entity import Category, Product
from src.modules.catalog.repository import CategoryRepository, ProductRepository
from src.modules.catalog.schemas import CategoryCreate, ProductCreate, ProductUpdate


class CatalogService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        products: ProductRepository | None = None,
        categories: CategoryRepository | None = None,
    ) -> None:
        self._session = session
        self._products = products or ProductRepository(session)
        self._categories = categories or CategoryRepository(session)
        self._audit = AuditService(session)

    async def list_products(
        self,
        *,
        tenant_id: UUID,
        search: str | None,
        category_id: UUID | None,
        page: int,
        page_size: int,
    ) -> tuple[list[Product], bool]:
        offset = max(0, (page - 1) * page_size)
        return await self._products.list(
            tenant_id=tenant_id,
            search=search,
            category_id=category_id,
            limit=page_size,
            offset=offset,
        )

    async def get_product(self, *, tenant_id: UUID, product_id: UUID) -> Product:
        product = await self._products.get(product_id, tenant_id=tenant_id)
        if product is None:
            raise NotFoundError("We couldn't find that product.")
        return product

    async def find_by_barcode(
        self, *, tenant_id: UUID, barcode: str
    ) -> Product | None:
        """Scanner lookup. Returns None when the barcode is unrecognised —
        callers (self-checkout, POS terminal) decide how to handle the miss."""
        return await self._products.get_by_barcode(barcode, tenant_id=tenant_id)

    async def create_product(
        self, *, tenant_id: UUID, actor_id: UUID | None, data: ProductCreate
    ) -> Product:
        product = Product(
            tenant_id=tenant_id,
            sku=data.sku,
            barcode=data.barcode,
            name=data.name,
            description=data.description,
            category_id=data.category_id,
            price_cents=data.price_cents,
            currency=data.currency.upper(),
            is_active=data.is_active,
            track_inventory=data.track_inventory,
            tax_rate=data.tax_rate,
            vertical_data=data.vertical_data,
        )
        await self._products.add(product)
        await self._audit.record(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="product.created",
            resource_type="product",
            resource_id=str(product.id),
            after={"sku": product.sku, "name": product.name, "price_cents": product.price_cents},
        )
        return product

    async def update_product(
        self, *, tenant_id: UUID, actor_id: UUID | None, product_id: UUID, data: ProductUpdate
    ) -> Product:
        product = await self.get_product(tenant_id=tenant_id, product_id=product_id)
        changes = data.model_dump(exclude_unset=True)
        before = {k: getattr(product, k) for k in changes if hasattr(product, k)}
        for field, value in changes.items():
            setattr(product, field, value)
        await self._session.flush()
        await self._audit.record(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="product.updated",
            resource_type="product",
            resource_id=str(product.id),
            before=_jsonable(before),
            after=_jsonable(changes),
        )
        return product

    async def delete_product(
        self, *, tenant_id: UUID, actor_id: UUID | None, product_id: UUID
    ) -> None:
        product = await self.get_product(tenant_id=tenant_id, product_id=product_id)
        await self._audit.record(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="product.deleted",
            resource_type="product",
            resource_id=str(product.id),
            before={"sku": product.sku, "name": product.name},
        )
        await self._products.delete(product)


def _jsonable(data: dict) -> dict:  # type: ignore[type-arg]
    """Make arbitrary mutation payloads JSON-safe for the audit log."""
    out: dict = {}
    for k, v in data.items():
        if hasattr(v, "isoformat"):
            out[k] = v.isoformat()
        elif hasattr(v, "__str__") and v.__class__.__name__ in {"UUID", "Decimal"}:
            out[k] = str(v)
        else:
            out[k] = v
    return out


class CategoryService:
    def __init__(
        self,
        session: AsyncSession,
        repo: CategoryRepository | None = None,
    ) -> None:
        self._session = session
        self._repo = repo or CategoryRepository(session)

    async def list(self, *, tenant_id: UUID) -> list[Category]:
        return await self._repo.list(tenant_id=tenant_id)

    async def create(self, *, tenant_id: UUID, data: CategoryCreate) -> Category:
        existing = await self._repo.by_slug(tenant_id=tenant_id, slug=data.slug)
        if existing is not None:
            raise ConflictError("A category with that slug already exists.")
        category = Category(
            tenant_id=tenant_id,
            slug=data.slug.lower(),
            name=data.name,
            parent_id=data.parent_id,
        )
        return await self._repo.add(category)
