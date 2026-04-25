"""Pharmacy — batch + expiry tracking, Rx records, controlled-substance flag."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class PharmacyBatch(Base):
    __tablename__ = "pharmacy_batches"
    __table_args__ = (
        UniqueConstraint("tenant_id", "product_id", "batch_no", name="uq_pharmacy_batch"),
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
    batch_no: Mapped[str] = mapped_column(String(64))
    expiry_date: Mapped[date] = mapped_column(Date)
    quantity_remaining: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class DrugMetadata(Base):
    """Per-product pharma attributes — controlled flag, schedule, dosage form."""

    __tablename__ = "pharmacy_drug_metadata"

    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    is_controlled: Mapped[bool] = mapped_column(Boolean, default=False)
    # Schedule (e.g. II/III/IV in the US, Class A/B/C in BD). Free-text so
    # tenants in different jurisdictions can use their local convention.
    schedule: Mapped[str | None] = mapped_column(String(16), default=None)
    dosage_form: Mapped[str | None] = mapped_column(String(32), default=None)
    strength: Mapped[str | None] = mapped_column(String(32), default=None)


class Prescription(Base):
    """Rx record tied to an order — required for controlled-substance sales."""

    __tablename__ = "pharmacy_prescriptions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    prescription_no: Mapped[str] = mapped_column(String(64))
    doctor_name: Mapped[str] = mapped_column(String(255))
    issued_on: Mapped[date] = mapped_column(Date)
    order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    customer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    doctor_license: Mapped[str | None] = mapped_column(String(64), default=None)
    notes: Mapped[str | None] = mapped_column(String(2048), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
