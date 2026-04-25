from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError, ValidationError
from src.verticals.deployment.softpos.entity import (
    SoftposReader,
    SoftposTapEvent,
    TapOutcome,
)


@dataclass(slots=True)
class ReaderActivity:
    reader_id: UUID
    since: datetime | None
    until: datetime | None
    events: list[SoftposTapEvent]
    approved_count: int
    declined_count: int
    cancelled_count: int
    error_count: int
    approved_amount_cents: int


class SoftposService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Readers
    # ──────────────────────────────────────────────

    async def register_reader(
        self,
        *,
        tenant_id: UUID,
        device_label: str,
        device_fingerprint: str,
    ) -> SoftposReader:
        stmt = select(SoftposReader).where(
            SoftposReader.tenant_id == tenant_id,
            SoftposReader.device_fingerprint == device_fingerprint,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            raise ConflictError("A reader with that device fingerprint is already registered.")

        reader = SoftposReader(
            tenant_id=tenant_id,
            device_label=device_label,
            device_fingerprint=device_fingerprint,
        )
        self._session.add(reader)
        await self._session.flush()
        return reader

    async def certify_reader(
        self, *, tenant_id: UUID, reader_id: UUID
    ) -> SoftposReader:
        reader = await self._get_reader(tenant_id=tenant_id, reader_id=reader_id)
        if reader.is_certified:
            return reader
        reader.is_certified = True
        reader.certified_at = datetime.now(tz=UTC)
        await self._session.flush()
        return reader

    async def list_readers(self, *, tenant_id: UUID) -> list[SoftposReader]:
        stmt = (
            select(SoftposReader)
            .where(SoftposReader.tenant_id == tenant_id)
            .order_by(SoftposReader.device_label)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def _get_reader(
        self, *, tenant_id: UUID, reader_id: UUID
    ) -> SoftposReader:
        reader = await self._session.get(SoftposReader, reader_id)
        if reader is None or reader.tenant_id != tenant_id:
            raise NotFoundError("Reader not found.")
        return reader

    # ──────────────────────────────────────────────
    # Tap events
    # ──────────────────────────────────────────────

    async def record_tap(
        self,
        *,
        tenant_id: UUID,
        reader_id: UUID,
        amount_cents: int,
        card_bin: str,
        outcome: TapOutcome,
        provider_reference: str | None = None,
    ) -> SoftposTapEvent:
        if len(card_bin) != 6 or not card_bin.isdigit():
            raise ValidationError("Card BIN must be exactly 6 digits.")
        reader = await self._get_reader(tenant_id=tenant_id, reader_id=reader_id)

        event = SoftposTapEvent(
            tenant_id=tenant_id,
            reader_id=reader.id,
            amount_cents=amount_cents,
            card_bin=card_bin,
            outcome=outcome,
            provider_reference=provider_reference,
        )
        self._session.add(event)

        reader.last_seen_at = datetime.now(tz=UTC)
        await self._session.flush()
        return event

    async def reader_activity(
        self,
        *,
        tenant_id: UUID,
        reader_id: UUID,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> ReaderActivity:
        reader = await self._get_reader(tenant_id=tenant_id, reader_id=reader_id)
        stmt = select(SoftposTapEvent).where(
            SoftposTapEvent.tenant_id == tenant_id,
            SoftposTapEvent.reader_id == reader.id,
        )
        if since is not None:
            stmt = stmt.where(SoftposTapEvent.tapped_at >= since)
        if until is not None:
            stmt = stmt.where(SoftposTapEvent.tapped_at <= until)
        stmt = stmt.order_by(SoftposTapEvent.tapped_at.desc())
        events = list((await self._session.execute(stmt)).scalars().all())

        approved = [e for e in events if e.outcome == TapOutcome.APPROVED]
        declined = [e for e in events if e.outcome == TapOutcome.DECLINED]
        cancelled = [e for e in events if e.outcome == TapOutcome.CANCELLED]
        errored = [e for e in events if e.outcome == TapOutcome.ERROR]

        return ReaderActivity(
            reader_id=reader.id,
            since=since,
            until=until,
            events=events,
            approved_count=len(approved),
            declined_count=len(declined),
            cancelled_count=len(cancelled),
            error_count=len(errored),
            approved_amount_cents=sum(e.amount_cents for e in approved),
        )
