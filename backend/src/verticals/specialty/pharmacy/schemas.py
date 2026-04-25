from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class BatchRead(CamelModel):
    id: UUID
    product_id: UUID
    batch_no: str
    expiry_date: date
    quantity_remaining: int


class BatchCreate(CamelModel):
    product_id: UUID
    batch_no: str = Field(min_length=1, max_length=64)
    expiry_date: date
    quantity: int = Field(ge=1)


class DrugMetadataUpsert(CamelModel):
    product_id: UUID
    is_controlled: bool = False
    schedule: str | None = Field(default=None, max_length=16)
    dosage_form: str | None = Field(default=None, max_length=32)
    strength: str | None = Field(default=None, max_length=32)


class DrugMetadataRead(CamelModel):
    product_id: UUID
    is_controlled: bool
    schedule: str | None
    dosage_form: str | None
    strength: str | None


class PrescriptionCreate(CamelModel):
    customer_id: UUID | None = None
    prescription_no: str = Field(min_length=1, max_length=64)
    doctor_name: str = Field(min_length=1, max_length=255)
    doctor_license: str | None = Field(default=None, max_length=64)
    issued_on: date
    notes: str | None = Field(default=None, max_length=2048)


class PrescriptionRead(CamelModel):
    id: UUID
    customer_id: UUID | None
    order_id: UUID | None
    prescription_no: str
    doctor_name: str
    doctor_license: str | None
    issued_on: date
    notes: str | None


class FefoDispatchRequest(CamelModel):
    product_id: UUID
    quantity: int = Field(ge=1)
    prescription_id: UUID | None = None


class FefoDispatchLine(CamelModel):
    batch_id: UUID
    batch_no: str
    quantity: int
