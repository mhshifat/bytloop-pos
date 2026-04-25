from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from pydantic import Field
from sqlalchemy import delete, select

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.core.schemas import CamelModel
from src.modules.procurement.entity import ProductSupplier

router = APIRouter(prefix="/product-suppliers", tags=["procurement"])


class ProductSupplierRead(CamelModel):
    id: UUID
    product_id: UUID
    supplier_id: UUID
    is_preferred: bool
    unit_cost_cents: int
    lead_time_days: int
    lead_time_std_days: int
    min_order_qty: int
    pack_size: int


class ProductSupplierUpsert(CamelModel):
    product_id: UUID
    supplier_id: UUID
    is_preferred: bool = False
    unit_cost_cents: int = Field(default=0, ge=0)
    lead_time_days: int = Field(default=7, ge=1, le=365)
    lead_time_std_days: int = Field(default=2, ge=0, le=365)
    min_order_qty: int = Field(default=1, ge=1, le=100000)
    pack_size: int = Field(default=1, ge=1, le=100000)


@router.get(
    "",
    response_model=list[ProductSupplierRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_product_suppliers(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    product_id: UUID | None = Query(default=None, alias="productId"),
    supplier_id: UUID | None = Query(default=None, alias="supplierId"),
) -> list[ProductSupplierRead]:
    stmt = select(ProductSupplier).where(ProductSupplier.tenant_id == user.tenant_id)
    if product_id is not None:
        stmt = stmt.where(ProductSupplier.product_id == product_id)
    if supplier_id is not None:
        stmt = stmt.where(ProductSupplier.supplier_id == supplier_id)
    stmt = stmt.order_by(ProductSupplier.is_preferred.desc(), ProductSupplier.updated_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return [ProductSupplierRead.model_validate(r) for r in rows]


@router.post(
    "",
    response_model=ProductSupplierRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def upsert_product_supplier(
    data: ProductSupplierUpsert,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ProductSupplierRead:
    existing = (
        await db.execute(
            select(ProductSupplier).where(
                ProductSupplier.tenant_id == user.tenant_id,
                ProductSupplier.product_id == data.product_id,
                ProductSupplier.supplier_id == data.supplier_id,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        existing = ProductSupplier(tenant_id=user.tenant_id, product_id=data.product_id, supplier_id=data.supplier_id)
        db.add(existing)
    existing.is_preferred = bool(data.is_preferred)
    existing.unit_cost_cents = int(data.unit_cost_cents)
    existing.lead_time_days = int(data.lead_time_days)
    existing.lead_time_std_days = int(data.lead_time_std_days)
    existing.min_order_qty = int(data.min_order_qty)
    existing.pack_size = int(data.pack_size)

    # If setting preferred, unset other preferred suppliers for this product.
    if existing.is_preferred:
        others = (
            await db.execute(
                select(ProductSupplier).where(
                    ProductSupplier.tenant_id == user.tenant_id,
                    ProductSupplier.product_id == data.product_id,
                    ProductSupplier.supplier_id != data.supplier_id,
                )
            )
        ).scalars().all()
        for o in others:
            o.is_preferred = False

    await db.flush()
    return ProductSupplierRead.model_validate(existing)


@router.delete(
    "",
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def delete_product_supplier(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    product_id: UUID = Query(alias="productId"),
    supplier_id: UUID = Query(alias="supplierId"),
) -> dict[str, bool]:
    await db.execute(
        delete(ProductSupplier).where(
            ProductSupplier.tenant_id == user.tenant_id,
            ProductSupplier.product_id == product_id,
            ProductSupplier.supplier_id == supplier_id,
        )
    )
    await db.flush()
    return {"ok": True}

