from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import Field, model_validator

from src.core.schemas import CamelModel
from src.verticals.services.patient_records.entity import PatientKind


class PatientRead(CamelModel):
    id: UUID
    customer_id: UUID | None
    kind: PatientKind
    first_name: str | None
    pet_name: str | None
    dob_or_birth_year: str | None
    species: str | None
    breed: str | None
    allergies: str | None
    notes: str | None


class PatientCreate(CamelModel):
    customer_id: UUID | None = None
    kind: PatientKind = PatientKind.PERSON
    first_name: str | None = Field(default=None, max_length=80)
    pet_name: str | None = Field(default=None, max_length=80)
    dob_or_birth_year: str | None = Field(default=None, max_length=16)
    species: str | None = Field(default=None, max_length=64)
    breed: str | None = Field(default=None, max_length=64)
    allergies: str | None = Field(default=None, max_length=2048)
    notes: str | None = Field(default=None, max_length=2048)

    @model_validator(mode="after")
    def _require_name_for_kind(self) -> PatientCreate:
        if self.kind == PatientKind.PERSON and not self.first_name:
            raise ValueError("first_name is required when kind=person")
        if self.kind == PatientKind.PET and not self.pet_name:
            raise ValueError("pet_name is required when kind=pet")
        return self


class VisitRead(CamelModel):
    id: UUID
    patient_id: UUID
    attending_user_id: UUID | None
    visit_date: date
    chief_complaint: str
    diagnosis: str | None
    treatment_notes: str | None
    order_id: UUID | None
    follow_up_on: date | None
    created_at: datetime


class VisitCreate(CamelModel):
    patient_id: UUID
    attending_user_id: UUID | None = None
    visit_date: date
    chief_complaint: str = Field(min_length=1, max_length=2048)
    diagnosis: str | None = Field(default=None, max_length=2048)
    treatment_notes: str | None = Field(default=None, max_length=4096)
    order_id: UUID | None = None
    follow_up_on: date | None = None


class PrescriptionRead(CamelModel):
    id: UUID
    patient_id: UUID
    visit_id: UUID | None
    medication_name: str
    dosage: str
    frequency: str
    duration_days: int
    prescribed_by_user_id: UUID | None
    created_at: datetime


class PrescriptionCreate(CamelModel):
    patient_id: UUID
    visit_id: UUID | None = None
    medication_name: str = Field(min_length=1, max_length=255)
    dosage: str = Field(min_length=1, max_length=128)
    frequency: str = Field(min_length=1, max_length=128)
    duration_days: int = Field(ge=0, default=0)
