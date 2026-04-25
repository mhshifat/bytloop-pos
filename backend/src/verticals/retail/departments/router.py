from __future__ import annotations

from datetime import datetime

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.retail.departments.schemas import (
    AssignProductRequest,
    CreateDepartmentRequest,
    DepartmentNode,
    DepartmentRead,
    DepartmentSalesRow,
    ProductDepartmentDetail,
    ProductDepartmentRead,
)
from src.verticals.retail.departments.service import DepartmentService

router = APIRouter(prefix="/departments", tags=["departments"])


@router.get(
    "",
    response_model=list[DepartmentNode],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_departments_tree(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[DepartmentNode]:
    return await DepartmentService(db).list_tree(tenant_id=user.tenant_id)


@router.post(
    "",
    response_model=DepartmentRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def create_department(
    req: CreateDepartmentRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DepartmentRead:
    dept = await DepartmentService(db).create_department(
        tenant_id=user.tenant_id,
        code=req.code,
        name=req.name,
        parent_id=req.parent_id,
    )
    return DepartmentRead.model_validate(dept)


@router.get(
    "/products/{product_id}",
    response_model=ProductDepartmentDetail,
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def get_product_department(
    product_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ProductDepartmentDetail:
    row = await DepartmentService(db).get_for_product(
        tenant_id=user.tenant_id, product_id=product_id
    )
    if row is None:
        from src.core.errors import NotFoundError

        raise NotFoundError("No department assigned to this product.")
    pd, dept = row
    return ProductDepartmentDetail(
        product_id=pd.product_id,
        department_id=pd.department_id,
        department_code=dept.code,
        department_name=dept.name,
    )


@router.post(
    "/assign",
    response_model=ProductDepartmentRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def assign_product(
    req: AssignProductRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ProductDepartmentRead:
    row = await DepartmentService(db).assign_product(
        tenant_id=user.tenant_id,
        product_id=req.product_id,
        department_id=req.department_id,
    )
    return ProductDepartmentRead.model_validate(row)


@router.get(
    "/reports/sales",
    response_model=list[DepartmentSalesRow],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def sales_by_department(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    since: datetime = Query(...),
    until: datetime = Query(...),
) -> list[DepartmentSalesRow]:
    return await DepartmentService(db).sales_by_department(
        tenant_id=user.tenant_id, since=since, until=until
    )
