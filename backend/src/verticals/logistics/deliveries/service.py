from __future__ import annotations

from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.verticals.logistics.deliveries.entity import (
    DeliverySchedule,
    DeliveryStatus,
)
from src.verticals.logistics.deliveries.schemas import ScheduleRequest


class DeliveryService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def schedule(
        self, *, tenant_id: UUID, data: ScheduleRequest
    ) -> DeliverySchedule:
        schedule = DeliverySchedule(
            tenant_id=tenant_id,
            order_id=data.order_id,
            address_line1=data.address_line1,
            address_line2=data.address_line2,
            city=data.city,
            postal_code=data.postal_code,
            country=data.country,
            recipient_name=data.recipient_name,
            recipient_phone=data.recipient_phone,
            scheduled_for=data.scheduled_for,
            delivered_at=None,
            delivery_fee_cents=data.delivery_fee_cents,
            status=DeliveryStatus.SCHEDULED,
            notes=data.notes,
        )
        self._session.add(schedule)
        await self._session.flush()
        return schedule

    async def get(
        self, *, tenant_id: UUID, delivery_id: UUID
    ) -> DeliverySchedule:
        schedule = await self._session.get(DeliverySchedule, delivery_id)
        if schedule is None or schedule.tenant_id != tenant_id:
            raise NotFoundError("Delivery not found.")
        return schedule

    async def mark_out_for_delivery(
        self, *, tenant_id: UUID, delivery_id: UUID
    ) -> DeliverySchedule:
        schedule = await self.get(tenant_id=tenant_id, delivery_id=delivery_id)
        if schedule.status not in (
            DeliveryStatus.SCHEDULED,
            DeliveryStatus.FAILED,
        ):
            raise ConflictError(
                "Only scheduled or failed deliveries can be sent out again."
            )
        schedule.status = DeliveryStatus.OUT_FOR_DELIVERY
        await self._session.flush()
        return schedule

    async def mark_delivered(
        self, *, tenant_id: UUID, delivery_id: UUID
    ) -> DeliverySchedule:
        schedule = await self.get(tenant_id=tenant_id, delivery_id=delivery_id)
        if schedule.status == DeliveryStatus.DELIVERED:
            return schedule
        schedule.status = DeliveryStatus.DELIVERED
        schedule.delivered_at = datetime.now(tz=UTC)
        await self._session.flush()
        return schedule

    async def mark_failed(
        self, *, tenant_id: UUID, delivery_id: UUID, reason: str
    ) -> DeliverySchedule:
        schedule = await self.get(tenant_id=tenant_id, delivery_id=delivery_id)
        if schedule.status == DeliveryStatus.DELIVERED:
            raise ConflictError("Already-delivered deliveries can't be marked failed.")
        schedule.status = DeliveryStatus.FAILED
        # Append rather than clobber prior notes, so the courier trail survives.
        stamp = datetime.now(tz=UTC).isoformat(timespec="seconds")
        suffix = f"[{stamp}] failed: {reason}"
        schedule.notes = (
            f"{schedule.notes}\n{suffix}" if schedule.notes else suffix
        )
        await self._session.flush()
        return schedule

    async def list_scheduled(
        self, *, tenant_id: UUID, day: date
    ) -> list[DeliverySchedule]:
        start = datetime.combine(day, time.min, tzinfo=UTC)
        end = start + timedelta(days=1)
        stmt = (
            select(DeliverySchedule)
            .where(
                DeliverySchedule.tenant_id == tenant_id,
                DeliverySchedule.scheduled_for >= start,
                DeliverySchedule.scheduled_for < end,
            )
            .order_by(DeliverySchedule.scheduled_for)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_for_order(
        self, *, tenant_id: UUID, order_id: UUID
    ) -> list[DeliverySchedule]:
        stmt = (
            select(DeliverySchedule)
            .where(
                DeliverySchedule.tenant_id == tenant_id,
                DeliverySchedule.order_id == order_id,
            )
            .order_by(DeliverySchedule.created_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())
