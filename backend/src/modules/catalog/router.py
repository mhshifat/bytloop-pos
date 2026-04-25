from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.modules.catalog.schemas import (
    CategoryCreate,
    CategoryRead,
    ProductCreate,
    ProductList,
    ProductRead,
    ProductUpdate,
)
from src.modules.catalog.service import CatalogService, CategoryService

router = APIRouter(prefix="/products", tags=["catalog"])
categories_router = APIRouter(prefix="/categories", tags=["catalog"])


@categories_router.get(
    "",
    response_model=list[CategoryRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_categories(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[CategoryRead]:
    rows = await CategoryService(db).list(tenant_id=user.tenant_id)
    return [CategoryRead.model_validate(r) for r in rows]


@categories_router.post(
    "",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def create_category(
    data: CategoryCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CategoryRead:
    category = await CategoryService(db).create(tenant_id=user.tenant_id, data=data)
    return CategoryRead.model_validate(category)


@router.get(
    "",
    response_model=ProductList,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_products(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    search: str | None = Query(default=None),
    category_id: UUID | None = Query(default=None, alias="categoryId"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100, alias="pageSize"),
) -> ProductList:
    items, has_more = await CatalogService(db).list_products(
        tenant_id=user.tenant_id,
        search=search,
        category_id=category_id,
        page=page,
        page_size=page_size,
    )
    return ProductList(
        items=[ProductRead.model_validate(p) for p in items],
        has_more=has_more,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=ProductRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def create_product(
    data: ProductCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ProductRead:
    product = await CatalogService(db).create_product(
        tenant_id=user.tenant_id, actor_id=user.id, data=data
    )
    return ProductRead.model_validate(product)


@router.get(
    "/{product_id}",
    response_model=ProductRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def get_product(
    product_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ProductRead:
    product = await CatalogService(db).get_product(
        tenant_id=user.tenant_id, product_id=product_id
    )
    return ProductRead.model_validate(product)


@router.patch(
    "/{product_id}",
    response_model=ProductRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def update_product(
    product_id: UUID,
    data: ProductUpdate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ProductRead:
    product = await CatalogService(db).update_product(
        tenant_id=user.tenant_id, actor_id=user.id, product_id=product_id, data=data
    )
    return ProductRead.model_validate(product)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def delete_product(
    product_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> None:
    await CatalogService(db).delete_product(
        tenant_id=user.tenant_id, actor_id=user.id, product_id=product_id
    )
