"""Retail departments — hierarchical store sections + per-department reporting.

Big-box and grocery formats organise inventory by department (Produce, Dairy,
Electronics...) with sub-sections under them. ``Department`` is a self-referential
tree; ``ProductDepartment`` is a 1-to-1 assignment table keyed by ``product_id``
so a product lives in exactly one department at a time. Sales reporting joins
through that assignment table so refunds and voids correctly net against the
same department the sale landed in.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class Department(Base):
    __tablename__ = "departments"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_departments_tenant_code"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    # Self-FK with SET NULL so deleting a parent promotes its children to
    # top-level instead of cascading and wiping a whole subtree.
    parent_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class ProductDepartment(Base):
    """One department per product — ``product_id`` is the PK.

    Re-assigning is a plain UPDATE on the same row rather than an insert,
    which keeps the cardinality invariant without an extra unique constraint.
    """

    __tablename__ = "product_departments"

    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    department_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("departments.id", ondelete="CASCADE"),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
