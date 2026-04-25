"""Resort — all-inclusive package billing layered on top of Hotel.

Two tables: a ``resort_packages`` catalog (price + what's bundled) and a
``resort_package_bookings`` row per reservation that attached a package.
The attachment is what actually moves money — we post the computed total
as a single folio charge on the reservation, so the existing hotel folio
endpoint renders package + incidentals without resort needing its own
accounting.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class ResortPackage(Base):
    __tablename__ = "resort_packages"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_resort_packages_tenant_code"),
    )

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    code: Mapped[str] = mapped_column(String(64))
    name: Mapped[str] = mapped_column(String(255))
    per_night_price_cents: Mapped[int] = mapped_column(default=0)
    includes_meals: Mapped[bool] = mapped_column(Boolean, default=True)
    includes_drinks: Mapped[bool] = mapped_column(Boolean, default=False)
    includes_spa: Mapped[bool] = mapped_column(Boolean, default=False)
    includes_activities: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class ResortPackageBooking(Base):
    """A package attached to a hotel reservation.

    We snapshot ``package_code`` and ``total_package_cents`` here rather
    than keep a live FK to ``resort_packages`` — if the package price is
    edited later, existing folios stay stable.
    """

    __tablename__ = "resort_package_bookings"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    reservation_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("hotel_reservations.id", ondelete="CASCADE"),
        index=True,
    )
    package_code: Mapped[str] = mapped_column(String(64))
    nights: Mapped[int] = mapped_column(default=1)
    total_package_cents: Mapped[int] = mapped_column(default=0)
    attached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
