from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel
from src.verticals.deployment.softpos.entity import TapOutcome


class SoftposReaderRead(CamelModel):
    id: UUID
    device_label: str
    device_fingerprint: str
    is_certified: bool
    certified_at: datetime | None = None
    last_seen_at: datetime | None = None


class RegisterReaderRequest(CamelModel):
    device_label: str = Field(min_length=1, max_length=128)
    device_fingerprint: str = Field(min_length=1, max_length=128)


class SoftposTapEventRead(CamelModel):
    id: UUID
    reader_id: UUID
    amount_cents: int
    card_bin: str
    outcome: TapOutcome
    provider_reference: str | None = None
    tapped_at: datetime


class RecordTapRequest(CamelModel):
    amount_cents: int = Field(ge=0)
    card_bin: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    outcome: TapOutcome
    provider_reference: str | None = Field(default=None, max_length=128)


class ReaderActivityRead(CamelModel):
    reader_id: UUID
    since: datetime | None = None
    until: datetime | None = None
    approved_count: int
    declined_count: int
    cancelled_count: int
    error_count: int
    approved_amount_cents: int
    events: list[SoftposTapEventRead]
