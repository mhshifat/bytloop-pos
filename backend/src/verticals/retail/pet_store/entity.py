"""Pet store — species/breed/life-stage metadata for pet products.

One row per pet-targeted ``Product``. ``product_id`` is both PK and FK —
there's no independent identity for the metadata beyond "the extra pet
columns for this product", and making it the PK gives us a free one-to-one
guarantee without a unique constraint. CASCADE on product delete because
orphaned metadata is never useful.

Every column except ``is_prescription_food`` is nullable: a generic food
brand may have no single target species; a toy may have no life stage.
Loose schema here beats inventing sentinels like "all".
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class PetProductMetadata(Base):
    __tablename__ = "pet_product_metadata"

    # product_id IS the primary key — one metadata row per product, enforced
    # at the schema level rather than via a unique constraint.
    product_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    target_species: Mapped[str | None] = mapped_column(String(32), default=None, index=True)
    target_breed: Mapped[str | None] = mapped_column(String(128), default=None)
    life_stage: Mapped[str | None] = mapped_column(String(32), default=None)
    weight_range_lbs: Mapped[str | None] = mapped_column(String(32), default=None)
    is_prescription_food: Mapped[bool] = mapped_column(
        Boolean, default=False, index=True
    )
