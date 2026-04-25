from __future__ import annotations

from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class PetProductMetadataRead(CamelModel):
    product_id: UUID
    target_species: str | None = None
    target_breed: str | None = None
    life_stage: str | None = None
    weight_range_lbs: str | None = None
    is_prescription_food: bool = False


class UpsertMetadataRequest(CamelModel):
    product_id: UUID
    target_species: str | None = Field(default=None, max_length=32)
    target_breed: str | None = Field(default=None, max_length=128)
    life_stage: str | None = Field(default=None, max_length=32)
    weight_range_lbs: str | None = Field(default=None, max_length=32)
    is_prescription_food: bool = False
