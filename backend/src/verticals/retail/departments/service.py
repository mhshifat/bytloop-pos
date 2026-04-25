from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError, ValidationError
from src.modules.catalog.api import Product
from src.modules.sales.api import Order, OrderItem, OrderStatus
from src.verticals.retail.departments.entity import Department, ProductDepartment
from src.verticals.retail.departments.schemas import (
    DepartmentNode,
    DepartmentSalesRow,
)


class DepartmentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_department(
        self,
        *,
        tenant_id: UUID,
        code: str,
        name: str,
        parent_id: UUID | None = None,
    ) -> Department:
        # Reject duplicate code for the same tenant up-front for a clean error.
        existing = (
            await self._session.execute(
                select(Department).where(
                    Department.tenant_id == tenant_id, Department.code == code
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            raise ConflictError("A department with that code already exists.")

        if parent_id is not None:
            parent = await self._session.get(Department, parent_id)
            if parent is None or parent.tenant_id != tenant_id:
                raise NotFoundError("Parent department not found.")

        dept = Department(
            tenant_id=tenant_id, code=code, name=name, parent_id=parent_id
        )
        self._session.add(dept)
        await self._session.flush()
        return dept

    async def list_tree(self, *, tenant_id: UUID) -> list[DepartmentNode]:
        stmt = (
            select(Department)
            .where(Department.tenant_id == tenant_id)
            .order_by(Department.code.asc())
        )
        rows = list((await self._session.execute(stmt)).scalars().all())

        # Build nodes keyed by id, then splice each into its parent's
        # children. Rows without a parent_id (or whose parent no longer
        # exists under this tenant — e.g. after SET NULL) become roots.
        nodes: dict[UUID, DepartmentNode] = {
            r.id: DepartmentNode(
                id=r.id, code=r.code, name=r.name, parent_id=r.parent_id, children=[]
            )
            for r in rows
        }
        roots: list[DepartmentNode] = []
        for r in rows:
            node = nodes[r.id]
            if r.parent_id is not None and r.parent_id in nodes:
                nodes[r.parent_id].children.append(node)
            else:
                roots.append(node)
        return roots

    async def get_for_product(
        self, *, tenant_id: UUID, product_id: UUID
    ) -> tuple[ProductDepartment, Department] | None:
        row = await self._session.get(ProductDepartment, product_id)
        if row is None or row.tenant_id != tenant_id:
            return None
        dept = await self._session.get(Department, row.department_id)
        if dept is None or dept.tenant_id != tenant_id:
            return None
        return (row, dept)

    async def assign_product(
        self, *, tenant_id: UUID, product_id: UUID, department_id: UUID
    ) -> ProductDepartment:
        # Validate that product and department both belong to this tenant.
        product = await self._session.get(Product, product_id)
        if product is None or product.tenant_id != tenant_id:
            raise NotFoundError("Product not found.")
        dept = await self._session.get(Department, department_id)
        if dept is None or dept.tenant_id != tenant_id:
            raise NotFoundError("Department not found.")

        existing = await self._session.get(ProductDepartment, product_id)
        if existing is not None:
            # Cross-tenant guard — a PK collision with another tenant's row
            # should look like a 404 to us, not a silent overwrite.
            if existing.tenant_id != tenant_id:
                raise ValidationError("Product is not owned by this tenant.")
            existing.department_id = department_id
            await self._session.flush()
            return existing

        row = ProductDepartment(
            product_id=product_id,
            tenant_id=tenant_id,
            department_id=department_id,
        )
        self._session.add(row)
        await self._session.flush()
        return row

    async def sales_by_department(
        self, *, tenant_id: UUID, since: datetime, until: datetime
    ) -> list[DepartmentSalesRow]:
        """Aggregate revenue + unit counts for completed orders in [since, until)."""
        stmt = (
            select(
                Department.id.label("department_id"),
                Department.name.label("name"),
                func.coalesce(func.sum(OrderItem.line_total_cents), 0).label(
                    "revenue_cents"
                ),
                func.coalesce(func.sum(OrderItem.quantity), 0).label("unit_count"),
            )
            .select_from(OrderItem)
            .join(Order, Order.id == OrderItem.order_id)
            .join(
                ProductDepartment,
                ProductDepartment.product_id == OrderItem.product_id,
            )
            .join(Department, Department.id == ProductDepartment.department_id)
            .where(
                Order.tenant_id == tenant_id,
                Order.status == OrderStatus.COMPLETED,
                Order.opened_at >= since,
                Order.opened_at < until,
            )
            .group_by(Department.id, Department.name)
            .order_by(func.sum(OrderItem.line_total_cents).desc())
        )
        result = await self._session.execute(stmt)
        return [
            DepartmentSalesRow(
                department_id=row.department_id,
                name=row.name,
                revenue_cents=int(row.revenue_cents),
                unit_count=int(row.unit_count),
            )
            for row in result
        ]
