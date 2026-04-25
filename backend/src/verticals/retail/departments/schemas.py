from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class DepartmentRead(CamelModel):
    id: UUID
    code: str
    name: str
    parent_id: UUID | None = None


class DepartmentNode(CamelModel):
    """Recursive tree node returned by ``list_tree``."""

    id: UUID
    code: str
    name: str
    parent_id: UUID | None = None
    children: list["DepartmentNode"] = Field(default_factory=list)


DepartmentNode.model_rebuild()


class CreateDepartmentRequest(CamelModel):
    code: str = Field(min_length=1, max_length=64)
    name: str = Field(min_length=1, max_length=255)
    parent_id: UUID | None = None


class AssignProductRequest(CamelModel):
    product_id: UUID
    department_id: UUID


class ProductDepartmentRead(CamelModel):
    product_id: UUID
    department_id: UUID


class ProductDepartmentDetail(CamelModel):
    """Product + department label for POS / labels."""

    product_id: UUID
    department_id: UUID
    department_code: str
    department_name: str


class DepartmentSalesRow(CamelModel):
    department_id: UUID
    name: str
    revenue_cents: int
    unit_count: int


class SalesReportQuery(CamelModel):
    since: datetime
    until: datetime
