from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, ForbiddenError, NotFoundError
from src.verticals.specialty.pharmacy.entity import (
    DrugMetadata,
    PharmacyBatch,
    Prescription,
)


class PharmacyService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Batches
    # ──────────────────────────────────────────────

    async def list_batches(
        self, *, tenant_id: UUID, product_id: UUID | None = None
    ) -> list[PharmacyBatch]:
        stmt = select(PharmacyBatch).where(PharmacyBatch.tenant_id == tenant_id)
        if product_id is not None:
            stmt = stmt.where(PharmacyBatch.product_id == product_id)
        stmt = stmt.order_by(PharmacyBatch.expiry_date)
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_expiring(
        self, *, tenant_id: UUID, before: date
    ) -> list[PharmacyBatch]:
        stmt = (
            select(PharmacyBatch)
            .where(
                PharmacyBatch.tenant_id == tenant_id,
                PharmacyBatch.expiry_date <= before,
                PharmacyBatch.quantity_remaining > 0,
            )
            .order_by(PharmacyBatch.expiry_date)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def record_batch(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        batch_no: str,
        expiry_date: date,
        quantity: int,
    ) -> PharmacyBatch:
        batch = PharmacyBatch(
            tenant_id=tenant_id,
            product_id=product_id,
            batch_no=batch_no,
            expiry_date=expiry_date,
            quantity_remaining=quantity,
        )
        self._session.add(batch)
        await self._session.flush()
        return batch

    # ──────────────────────────────────────────────
    # FEFO dispatch — First Expired, First Out
    # ──────────────────────────────────────────────

    async def dispatch_fefo(
        self, *, tenant_id: UUID, product_id: UUID, quantity: int
    ) -> list[tuple[PharmacyBatch, int]]:
        """Pull stock from batches in expiry order until ``quantity`` is met.

        Returns the list of (batch, quantity_taken) so the caller can log
        which batch each consumed unit came from. Raises ``ConflictError``
        if there isn't enough unexpired stock to cover the request.
        """
        if quantity <= 0:
            return []
        today = date.today()
        stmt = (
            select(PharmacyBatch)
            .where(
                PharmacyBatch.tenant_id == tenant_id,
                PharmacyBatch.product_id == product_id,
                PharmacyBatch.quantity_remaining > 0,
                PharmacyBatch.expiry_date >= today,
            )
            .order_by(PharmacyBatch.expiry_date)
        )
        batches = list((await self._session.execute(stmt)).scalars().all())

        remaining = quantity
        taken: list[tuple[PharmacyBatch, int]] = []
        for batch in batches:
            if remaining <= 0:
                break
            take = min(batch.quantity_remaining, remaining)
            batch.quantity_remaining -= take
            remaining -= take
            taken.append((batch, take))
        if remaining > 0:
            # Roll back the in-memory deductions so caller can retry cleanly
            for batch, take in taken:
                batch.quantity_remaining += take
            raise ConflictError(
                f"Not enough unexpired stock for product: short by {remaining}."
            )
        await self._session.flush()
        return taken

    # ──────────────────────────────────────────────
    # Drug metadata + controlled-substance gate
    # ──────────────────────────────────────────────

    async def upsert_metadata(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        is_controlled: bool,
        schedule: str | None,
        dosage_form: str | None,
        strength: str | None,
    ) -> DrugMetadata:
        stmt = select(DrugMetadata).where(DrugMetadata.product_id == product_id)
        existing = (await self._session.execute(stmt)).scalar_one_or_none()
        if existing is not None and existing.tenant_id == tenant_id:
            existing.is_controlled = is_controlled
            existing.schedule = schedule
            existing.dosage_form = dosage_form
            existing.strength = strength
            await self._session.flush()
            return existing
        if existing is not None and existing.tenant_id != tenant_id:
            # Defensive against IDOR / cross-tenant UUID guessing: a product_id
            # from another tenant must not be mutable.
            raise ForbiddenError("You don't have permission to do that.")
        meta = DrugMetadata(
            product_id=product_id,
            tenant_id=tenant_id,
            is_controlled=is_controlled,
            schedule=schedule,
            dosage_form=dosage_form,
            strength=strength,
        )
        self._session.add(meta)
        await self._session.flush()
        return meta

    async def get_metadata(
        self, *, tenant_id: UUID, product_id: UUID
    ) -> DrugMetadata | None:
        stmt = select(DrugMetadata).where(
            DrugMetadata.tenant_id == tenant_id,
            DrugMetadata.product_id == product_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def assert_dispensable(
        self,
        *,
        tenant_id: UUID,
        product_id: UUID,
        prescription_id: UUID | None,
    ) -> None:
        """Refuse controlled-substance dispense without a prescription on file.

        The service is the gate, not the router — so any future path that
        sells drugs (sales.checkout, bulk-receive, etc.) gets the same check.
        """
        meta = await self.get_metadata(tenant_id=tenant_id, product_id=product_id)
        if meta is None or not meta.is_controlled:
            return
        if prescription_id is None:
            raise ForbiddenError(
                "This is a controlled substance. A prescription is required.",
                code="prescription_required",
            )
        rx = await self._session.get(Prescription, prescription_id)
        if rx is None or rx.tenant_id != tenant_id:
            raise NotFoundError("Prescription not found.")

    # ──────────────────────────────────────────────
    # Prescriptions
    # ──────────────────────────────────────────────

    async def create_prescription(
        self,
        *,
        tenant_id: UUID,
        customer_id: UUID | None,
        prescription_no: str,
        doctor_name: str,
        doctor_license: str | None,
        issued_on: date,
        notes: str | None = None,
    ) -> Prescription:
        rx = Prescription(
            tenant_id=tenant_id,
            customer_id=customer_id,
            prescription_no=prescription_no,
            doctor_name=doctor_name,
            doctor_license=doctor_license,
            issued_on=issued_on,
            notes=notes,
        )
        self._session.add(rx)
        await self._session.flush()
        return rx

    async def list_prescriptions(
        self, *, tenant_id: UUID, customer_id: UUID | None = None
    ) -> list[Prescription]:
        stmt = select(Prescription).where(Prescription.tenant_id == tenant_id)
        if customer_id is not None:
            stmt = stmt.where(Prescription.customer_id == customer_id)
        stmt = stmt.order_by(Prescription.issued_on.desc())
        return list((await self._session.execute(stmt)).scalars().all())

    # ──────────────────────────────────────────────
    # Alerts
    # ──────────────────────────────────────────────

    async def expiring_within_days(
        self, *, tenant_id: UUID, days: int = 90
    ) -> list[PharmacyBatch]:
        return await self.list_expiring(
            tenant_id=tenant_id, before=date.today() + timedelta(days=days)
        )
