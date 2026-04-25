from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class SegmentRead(CamelModel):
    id: UUID
    name: str
    kind: str
    definition: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class SegmentMemberRead(CamelModel):
    customer_id: UUID
    score: float
    meta: dict[str, Any] = Field(default_factory=dict)
    refreshed_at: datetime


class SegmentRecomputeResult(CamelModel):
    segments_created: int
    memberships_written: int


class CampaignTriggerRead(CamelModel):
    id: UUID
    segment_id: UUID | None
    channel: str
    threshold: float
    subject: str
    html_template: str
    discount_code: str | None
    cooldown_days: int
    enabled: bool
    created_at: datetime


class CampaignTriggerUpsert(CamelModel):
    segment_id: UUID | None = None
    threshold: float = Field(default=0.6, ge=0.0, le=1.0)
    subject: str = Field(default="", max_length=255)
    html_template: str = Field(default="", max_length=8000)
    discount_code: str | None = Field(default=None, max_length=64)
    cooldown_days: int = Field(default=14, ge=1, le=365)
    enabled: bool = False

