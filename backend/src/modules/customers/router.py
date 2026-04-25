from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.modules.customers.schemas import (
    CustomerCreate,
    CustomerList,
    CustomerRead,
    CustomerUpdate,
)
from src.modules.customers.service import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("", response_model=CustomerList, dependencies=[Depends(requires(Permission.PRODUCTS_READ))])
async def list_customers(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100, alias="pageSize"),
) -> CustomerList:
    items, has_more = await CustomerService(db).list(
        tenant_id=user.tenant_id, search=search, page=page, page_size=page_size
    )
    return CustomerList(
        items=[CustomerRead.model_validate(c) for c in items],
        has_more=has_more,
        page=page,
        page_size=page_size,
    )


@router.post(
    "",
    response_model=CustomerRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def create_customer(
    data: CustomerCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CustomerRead:
    customer = await CustomerService(db).create(
        tenant_id=user.tenant_id, actor_id=user.id, data=data
    )
    return CustomerRead.model_validate(customer)


@router.get(
    "/{customer_id}",
    response_model=CustomerRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def get_customer(
    customer_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CustomerRead:
    customer = await CustomerService(db).get(
        tenant_id=user.tenant_id, customer_id=customer_id
    )
    return CustomerRead.model_validate(customer)


@router.patch(
    "/{customer_id}",
    response_model=CustomerRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def update_customer(
    customer_id: UUID,
    data: CustomerUpdate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CustomerRead:
    customer = await CustomerService(db).update(
        tenant_id=user.tenant_id, customer_id=customer_id, data=data
    )
    return CustomerRead.model_validate(customer)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def delete_customer(
    customer_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> None:
    await CustomerService(db).delete(tenant_id=user.tenant_id, customer_id=customer_id)
