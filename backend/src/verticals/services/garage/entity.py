"""Garage — vehicle profile + job cards."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class JobCardStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    DELIVERED = "delivered"


class Vehicle(Base):
    __tablename__ = "vehicles"
    __table_args__ = (UniqueConstraint("tenant_id", "plate", name="uq_vehicles_tenant_plate"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    plate: Mapped[str] = mapped_column(String(16))
    make: Mapped[str] = mapped_column(String(64))
    model: Mapped[str] = mapped_column(String(64))
    customer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("customers.id", ondelete="SET NULL"), default=None
    )
    year: Mapped[int | None] = mapped_column(default=None)
    vin: Mapped[str | None] = mapped_column(String(32), default=None)


class JobCard(Base):
    __tablename__ = "job_cards"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    vehicle_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("vehicles.id", ondelete="RESTRICT"), index=True
    )
    order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), default=None
    )
    technician_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    status: Mapped[JobCardStatus] = mapped_column(String(16), default=JobCardStatus.OPEN)
    description: Mapped[str] = mapped_column(String(2048), default="")
    opened_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), default=None)


class JobLineKind(StrEnum):
    PART = "part"
    LABOR = "labor"


class JobLine(Base):
    """Billable line on a job card — either a part sold or a labor charge.

    Keeping them in a single table with a ``kind`` discriminator keeps the
    invoice simple; reports can still slice by kind when needed.
    """

    __tablename__ = "job_card_lines"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    job_card_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("job_cards.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[JobLineKind] = mapped_column(String(16))
    description: Mapped[str] = mapped_column(String(255))
    # For a part, link to the catalog product; labor lines leave this null.
    product_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="SET NULL"), default=None
    )
    quantity: Mapped[int] = mapped_column(default=1)  # parts: units, labor: minutes
    unit_cost_cents: Mapped[int] = mapped_column(default=0)
    line_total_cents: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
