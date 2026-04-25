from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError
from src.verticals.services.garage.entity import (
    JobCard,
    JobCardStatus,
    JobLine,
    JobLineKind,
    Vehicle,
)


class GarageService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def register_vehicle(
        self,
        *,
        tenant_id: UUID,
        customer_id: UUID | None,
        plate: str,
        make: str,
        model: str,
        year: int | None,
        vin: str | None,
    ) -> Vehicle:
        vehicle = Vehicle(
            tenant_id=tenant_id,
            customer_id=customer_id,
            plate=plate.upper(),
            make=make,
            model=model,
            year=year,
            vin=vin,
        )
        self._session.add(vehicle)
        await self._session.flush()
        return vehicle

    async def list_vehicles(self, *, tenant_id: UUID) -> list[Vehicle]:
        stmt = (
            select(Vehicle).where(Vehicle.tenant_id == tenant_id).order_by(Vehicle.plate)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def open_job(
        self,
        *,
        tenant_id: UUID,
        vehicle_id: UUID,
        description: str,
        technician_id: UUID | None,
    ) -> JobCard:
        job = JobCard(
            tenant_id=tenant_id,
            vehicle_id=vehicle_id,
            order_id=None,
            technician_id=technician_id,
            status=JobCardStatus.OPEN,
            description=description,
            closed_at=None,
        )
        self._session.add(job)
        await self._session.flush()
        return job

    async def list_open_jobs(self, *, tenant_id: UUID) -> list[JobCard]:
        stmt = (
            select(JobCard)
            .where(
                JobCard.tenant_id == tenant_id,
                JobCard.status.in_(
                    [JobCardStatus.OPEN, JobCardStatus.IN_PROGRESS, JobCardStatus.COMPLETED]
                ),
            )
            .order_by(JobCard.opened_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def update_job_status(
        self, *, tenant_id: UUID, job_id: UUID, status: JobCardStatus
    ) -> JobCard:
        job = await self._session.get(JobCard, job_id)
        if job is None or job.tenant_id != tenant_id:
            raise NotFoundError("Job card not found.")
        job.status = status
        await self._session.flush()
        return job

    # ──────────────────────────────────────────────
    # Job lines (parts + labor)
    # ──────────────────────────────────────────────

    async def add_line(
        self,
        *,
        tenant_id: UUID,
        job_id: UUID,
        kind: JobLineKind,
        description: str,
        quantity: int,
        unit_cost_cents: int,
        product_id: UUID | None = None,
    ) -> JobLine:
        job = await self._session.get(JobCard, job_id)
        if job is None or job.tenant_id != tenant_id:
            raise NotFoundError("Job card not found.")
        line = JobLine(
            tenant_id=tenant_id,
            job_card_id=job_id,
            kind=kind,
            product_id=product_id,
            description=description,
            quantity=quantity,
            unit_cost_cents=unit_cost_cents,
            line_total_cents=unit_cost_cents * quantity,
        )
        self._session.add(line)
        await self._session.flush()
        return line

    async def remove_line(
        self, *, tenant_id: UUID, line_id: UUID
    ) -> None:
        line = await self._session.get(JobLine, line_id)
        if line is None or line.tenant_id != tenant_id:
            raise NotFoundError("Job line not found.")
        await self._session.delete(line)
        await self._session.flush()

    async def list_lines(
        self, *, tenant_id: UUID, job_id: UUID
    ) -> list[JobLine]:
        stmt = (
            select(JobLine)
            .where(JobLine.tenant_id == tenant_id, JobLine.job_card_id == job_id)
            .order_by(JobLine.created_at)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def job_totals(
        self, *, tenant_id: UUID, job_id: UUID
    ) -> dict[str, int]:
        """Aggregate parts, labor, and grand total for a job card."""
        lines = await self.list_lines(tenant_id=tenant_id, job_id=job_id)
        parts = sum(
            l.line_total_cents for l in lines if l.kind == JobLineKind.PART
        )
        labor = sum(
            l.line_total_cents for l in lines if l.kind == JobLineKind.LABOR
        )
        return {
            "partsCents": parts,
            "laborCents": labor,
            "totalCents": parts + labor,
        }

    # ──────────────────────────────────────────────
    # Vehicle history
    # ──────────────────────────────────────────────

    async def vehicle_history(
        self, *, tenant_id: UUID, vehicle_id: UUID
    ) -> list[JobCard]:
        """All job cards (incl. closed) for a vehicle, most recent first."""
        stmt = (
            select(JobCard)
            .where(
                JobCard.tenant_id == tenant_id,
                JobCard.vehicle_id == vehicle_id,
            )
            .order_by(JobCard.opened_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
