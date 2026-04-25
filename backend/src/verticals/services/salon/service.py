from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.verticals.services.salon.entity import (
    AppointmentStatus,
    SalonAppointment,
    SalonService as SalonServiceEntity,
)


class SalonService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Service catalog
    # ──────────────────────────────────────────────

    async def list_services(self, *, tenant_id: UUID) -> list[SalonServiceEntity]:
        stmt = (
            select(SalonServiceEntity)
            .where(SalonServiceEntity.tenant_id == tenant_id)
            .order_by(SalonServiceEntity.name)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def upsert_service(
        self,
        *,
        tenant_id: UUID,
        code: str,
        name: str,
        duration_minutes: int,
        price_cents: int,
        product_id: UUID | None = None,
        is_active: bool = True,
    ) -> SalonServiceEntity:
        stmt = select(SalonServiceEntity).where(
            SalonServiceEntity.tenant_id == tenant_id,
            SalonServiceEntity.code == code,
        )
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None:
            existing.name = name
            existing.duration_minutes = duration_minutes
            existing.price_cents = price_cents
            existing.product_id = product_id
            existing.is_active = is_active
            await self._session.flush()
            return existing
        service = SalonServiceEntity(
            tenant_id=tenant_id,
            code=code,
            name=name,
            duration_minutes=duration_minutes,
            price_cents=price_cents,
            product_id=product_id,
            is_active=is_active,
        )
        self._session.add(service)
        await self._session.flush()
        return service

    # ──────────────────────────────────────────────
    # Appointments + availability
    # ──────────────────────────────────────────────

    async def list_appointments(
        self, *, tenant_id: UUID, start: datetime, end: datetime
    ) -> list[SalonAppointment]:
        stmt = (
            select(SalonAppointment)
            .where(
                SalonAppointment.tenant_id == tenant_id,
                SalonAppointment.starts_at >= start,
                SalonAppointment.starts_at < end,
            )
            .order_by(SalonAppointment.starts_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def _has_stylist_conflict(
        self,
        *,
        tenant_id: UUID,
        staff_id: UUID,
        starts_at: datetime,
        ends_at: datetime,
        exclude_appointment_id: UUID | None = None,
    ) -> bool:
        stmt = select(SalonAppointment).where(
            SalonAppointment.tenant_id == tenant_id,
            SalonAppointment.staff_id == staff_id,
            SalonAppointment.status.in_(
                [AppointmentStatus.BOOKED, AppointmentStatus.CHECKED_IN]
            ),
            and_(
                or_(
                    and_(
                        SalonAppointment.starts_at < ends_at,
                        SalonAppointment.ends_at > starts_at,
                    ),
                ),
            ),
        )
        if exclude_appointment_id is not None:
            stmt = stmt.where(SalonAppointment.id != exclude_appointment_id)
        result = (await self._session.execute(stmt)).scalars().first()
        return result is not None

    async def stylist_availability(
        self,
        *,
        tenant_id: UUID,
        staff_id: UUID,
        day_start: datetime,
        day_end: datetime,
    ) -> list[tuple[datetime, datetime]]:
        """Return busy windows for the given stylist on the given day."""
        stmt = (
            select(SalonAppointment)
            .where(
                SalonAppointment.tenant_id == tenant_id,
                SalonAppointment.staff_id == staff_id,
                SalonAppointment.status.in_(
                    [AppointmentStatus.BOOKED, AppointmentStatus.CHECKED_IN]
                ),
                SalonAppointment.starts_at >= day_start,
                SalonAppointment.starts_at < day_end,
            )
            .order_by(SalonAppointment.starts_at)
        )
        rows = list((await self._session.execute(stmt)).scalars().all())
        return [(r.starts_at, r.ends_at) for r in rows]

    async def book(
        self,
        *,
        tenant_id: UUID,
        customer_id: UUID,
        staff_id: UUID | None,
        service_id: UUID | None,
        service_name: str,
        starts_at: datetime,
        ends_at: datetime,
    ) -> SalonAppointment:
        if ends_at <= starts_at:
            raise ConflictError("Appointment end must be after its start.")
        if staff_id is not None and await self._has_stylist_conflict(
            tenant_id=tenant_id,
            staff_id=staff_id,
            starts_at=starts_at,
            ends_at=ends_at,
        ):
            raise ConflictError("That stylist is already booked in that window.")
        appt = SalonAppointment(
            tenant_id=tenant_id,
            customer_id=customer_id,
            staff_id=staff_id,
            service_id=service_id,
            service_name=service_name,
            status=AppointmentStatus.BOOKED,
            starts_at=starts_at,
            ends_at=ends_at,
            order_id=None,
        )
        self._session.add(appt)
        await self._session.flush()
        return appt

    async def update_status(
        self, *, tenant_id: UUID, appointment_id: UUID, status: AppointmentStatus
    ) -> SalonAppointment:
        appt = await self._session.get(SalonAppointment, appointment_id)
        if appt is None or appt.tenant_id != tenant_id:
            raise NotFoundError("Appointment not found.")
        appt.status = status
        await self._session.flush()
        return appt

    async def check_in_to_cart(
        self, *, tenant_id: UUID, appointment_id: UUID
    ) -> tuple[SalonAppointment, UUID | None]:
        """Mark appointment as checked-in; return the linked product_id so
        the POS can add the service to the current cart.
        """
        appt = await self._session.get(SalonAppointment, appointment_id)
        if appt is None or appt.tenant_id != tenant_id:
            raise NotFoundError("Appointment not found.")
        if appt.status not in (AppointmentStatus.BOOKED, AppointmentStatus.CHECKED_IN):
            raise ConflictError(
                "Only booked or already checked-in appointments can check in."
            )
        appt.status = AppointmentStatus.CHECKED_IN
        await self._session.flush()

        product_id: UUID | None = None
        if appt.service_id is not None:
            svc = await self._session.get(SalonServiceEntity, appt.service_id)
            if svc is not None and svc.product_id is not None:
                product_id = svc.product_id
        return appt, product_id
