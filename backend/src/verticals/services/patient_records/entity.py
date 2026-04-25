"""Patient records — shared chart module for dental / medical / veterinary POS.

One `Patient` entity with a `kind` discriminator so a vet clinic can register
pets (kind=pet, species/breed populated) while a dental practice uses the same
table for people (kind=person). The linked `customer_id` is the human payer —
for a vet, that's the pet's owner.
"""

from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class PatientKind(StrEnum):
    PERSON = "person"
    PET = "pet"


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    # For vets this is the owner; for dental/medical it's usually the patient
    # themselves (but may differ for pediatric patients, hence nullable).
    customer_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    kind: Mapped[PatientKind] = mapped_column(String(16), default=PatientKind.PERSON)
    # Person name (for PERSON) OR pet name (for PET) — stored in one nullable
    # column each so queries don't need a CASE. Exactly one is required per kind.
    first_name: Mapped[str | None] = mapped_column(String(80), default=None)
    pet_name: Mapped[str | None] = mapped_column(String(80), default=None)
    dob_or_birth_year: Mapped[str | None] = mapped_column(String(16), default=None)
    species: Mapped[str | None] = mapped_column(String(64), default=None)
    breed: Mapped[str | None] = mapped_column(String(64), default=None)
    allergies: Mapped[str | None] = mapped_column(String(2048), default=None)
    notes: Mapped[str | None] = mapped_column(String(2048), default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class Visit(Base):
    __tablename__ = "patient_visits"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    visit_date: Mapped[date] = mapped_column(Date)
    chief_complaint: Mapped[str] = mapped_column(String(2048))
    attending_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    diagnosis: Mapped[str | None] = mapped_column(String(2048), default=None)
    treatment_notes: Mapped[str | None] = mapped_column(String(4096), default=None)
    order_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    follow_up_on: Mapped[date | None] = mapped_column(Date, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class Prescription(Base):
    """Patient-chart prescription. Separate from the pharmacy-module Rx record,
    which is the dispensable artifact — this one is the clinical instruction
    on the patient's chart at visit time."""

    __tablename__ = "patient_prescriptions"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    patient_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    medication_name: Mapped[str] = mapped_column(String(255))
    dosage: Mapped[str] = mapped_column(String(128))
    frequency: Mapped[str] = mapped_column(String(128))
    visit_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("patient_visits.id", ondelete="SET NULL"),
        default=None,
        index=True,
    )
    duration_days: Mapped[int] = mapped_column(default=0)
    prescribed_by_user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
