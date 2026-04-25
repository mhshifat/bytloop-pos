from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class Planogram(Base):
    __tablename__ = "planograms"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    location_name: Mapped[str] = mapped_column(String(255), default="")
    # MVP: expected is a JSON object like { "expectedSkus": ["SKU1","SKU2", ...] }
    expected: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )


class PlanogramScan(Base):
    __tablename__ = "planogram_scans"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    tenant_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    planogram_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True), ForeignKey("planograms.id", ondelete="SET NULL"), nullable=True, index=True
    )
    image_public_id: Mapped[str] = mapped_column(String(512))
    result: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )

