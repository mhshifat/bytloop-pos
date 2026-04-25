"""Restaurant vertical — tables, Kitchen Order Tickets (KOT), KDS queues.

Extends core sales with F&B specifics. Table state is mastered here; KOT
items snapshot the order line at fire time so the kitchen sees an immutable
ticket even if the order is later edited.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class TableStatus(StrEnum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    RESERVED = "reserved"
    CLEANING = "cleaning"


class KdsStation(StrEnum):
    KITCHEN = "kitchen"
    BAR = "bar"
    DESSERT = "dessert"
    EXPO = "expo"


class KotStatus(StrEnum):
    NEW = "new"
    PREPARING = "preparing"
    READY = "ready"
    SERVED = "served"
    CANCELLED = "cancelled"


class RestaurantTable(Base):
    __tablename__ = "restaurant_tables"
    __table_args__ = (UniqueConstraint("tenant_id", "code", name="uq_tables_tenant_code"),)

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    location_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(16))
    label: Mapped[str] = mapped_column(String(64))
    seats: Mapped[int] = mapped_column(default=4)
    status: Mapped[TableStatus] = mapped_column(String(16), default=TableStatus.AVAILABLE)
    current_order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class KotTicket(Base):
    __tablename__ = "kot_tickets"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    order_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), index=True
    )
    station: Mapped[KdsStation] = mapped_column(String(16))
    number: Mapped[str] = mapped_column(String(16), index=True)
    status: Mapped[KotStatus] = mapped_column(String(16), default=KotStatus.NEW)
    # Course number (1=starters, 2=mains, 3=dessert) — kitchen fires in order.
    course: Mapped[int] = mapped_column(default=1)
    fired_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    ready_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )


class ProductStationRoute(Base):
    """Per-tenant rule: this product auto-fires to this station + course."""

    __tablename__ = "product_station_routes"
    __table_args__ = (
        UniqueConstraint("tenant_id", "product_id", name="uq_product_station_route"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="CASCADE"), index=True
    )
    station: Mapped[KdsStation] = mapped_column(String(16))
    course: Mapped[int] = mapped_column(default=1)


class KotItem(Base):
    """Line snapshot — immutable copy of what was ordered at fire time."""

    __tablename__ = "kot_items"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    ticket_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("kot_tickets.id", ondelete="CASCADE"), index=True
    )
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("products.id", ondelete="RESTRICT")
    )
    name_snapshot: Mapped[str] = mapped_column(String(255))
    quantity: Mapped[int] = mapped_column(default=1)
    modifier_notes: Mapped[str | None] = mapped_column(String(512), default=None)
