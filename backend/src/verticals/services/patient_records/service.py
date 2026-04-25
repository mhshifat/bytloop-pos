from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError, ValidationError
from src.verticals.services.patient_records.entity import (
    Patient,
    PatientKind,
    Prescription,
    Visit,
)


class PatientRecordsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Patients
    # ──────────────────────────────────────────────

    async def register_patient(
        self,
        *,
        tenant_id: UUID,
        customer_id: UUID | None,
        kind: PatientKind,
        first_name: str | None,
        pet_name: str | None,
        dob_or_birth_year: str | None,
        species: str | None,
        breed: str | None,
        allergies: str | None,
        notes: str | None,
    ) -> Patient:
        if kind == PatientKind.PERSON and not first_name:
            raise ValidationError("first_name is required for kind=person.")
        if kind == PatientKind.PET and not pet_name:
            raise ValidationError("pet_name is required for kind=pet.")
        patient = Patient(
            tenant_id=tenant_id,
            customer_id=customer_id,
            kind=kind,
            first_name=first_name,
            pet_name=pet_name,
            dob_or_birth_year=dob_or_birth_year,
            species=species if kind == PatientKind.PET else None,
            breed=breed if kind == PatientKind.PET else None,
            allergies=allergies,
            notes=notes,
        )
        self._session.add(patient)
        await self._session.flush()
        return patient

    async def get_patient(self, *, tenant_id: UUID, patient_id: UUID) -> Patient:
        patient = await self._session.get(Patient, patient_id)
        if patient is None or patient.tenant_id != tenant_id:
            raise NotFoundError("Patient not found.")
        return patient

    async def list_patients(
        self, *, tenant_id: UUID, search: str | None = None
    ) -> list[Patient]:
        stmt = select(Patient).where(Patient.tenant_id == tenant_id)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    Patient.first_name.ilike(like),
                    Patient.pet_name.ilike(like),
                )
            )
        stmt = stmt.order_by(Patient.created_at.desc())
        return list((await self._session.execute(stmt)).scalars().all())

    # ──────────────────────────────────────────────
    # Visits
    # ──────────────────────────────────────────────

    async def create_visit(
        self,
        *,
        tenant_id: UUID,
        patient_id: UUID,
        attending_user_id: UUID | None,
        visit_date: date,
        chief_complaint: str,
        diagnosis: str | None = None,
        treatment_notes: str | None = None,
        order_id: UUID | None = None,
        follow_up_on: date | None = None,
    ) -> Visit:
        # Make sure the patient actually belongs to this tenant before we
        # attach visits to it.
        await self.get_patient(tenant_id=tenant_id, patient_id=patient_id)
        visit = Visit(
            tenant_id=tenant_id,
            patient_id=patient_id,
            attending_user_id=attending_user_id,
            visit_date=visit_date,
            chief_complaint=chief_complaint,
            diagnosis=diagnosis,
            treatment_notes=treatment_notes,
            order_id=order_id,
            follow_up_on=follow_up_on,
        )
        self._session.add(visit)
        await self._session.flush()
        return visit

    async def visit_history(
        self, *, tenant_id: UUID, patient_id: UUID
    ) -> list[Visit]:
        await self.get_patient(tenant_id=tenant_id, patient_id=patient_id)
        stmt = (
            select(Visit)
            .where(Visit.tenant_id == tenant_id, Visit.patient_id == patient_id)
            .order_by(Visit.visit_date.desc(), Visit.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    # ──────────────────────────────────────────────
    # Prescriptions
    # ──────────────────────────────────────────────

    async def add_prescription(
        self,
        *,
        tenant_id: UUID,
        patient_id: UUID,
        visit_id: UUID | None,
        medication_name: str,
        dosage: str,
        frequency: str,
        duration_days: int,
        prescribed_by_user_id: UUID | None,
    ) -> Prescription:
        await self.get_patient(tenant_id=tenant_id, patient_id=patient_id)
        if visit_id is not None:
            visit = await self._session.get(Visit, visit_id)
            if visit is None or visit.tenant_id != tenant_id:
                raise NotFoundError("Visit not found.")
        rx = Prescription(
            tenant_id=tenant_id,
            patient_id=patient_id,
            visit_id=visit_id,
            medication_name=medication_name,
            dosage=dosage,
            frequency=frequency,
            duration_days=duration_days,
            prescribed_by_user_id=prescribed_by_user_id,
        )
        self._session.add(rx)
        await self._session.flush()
        return rx

    async def list_prescriptions(
        self, *, tenant_id: UUID, patient_id: UUID
    ) -> list[Prescription]:
        await self.get_patient(tenant_id=tenant_id, patient_id=patient_id)
        stmt = (
            select(Prescription)
            .where(
                Prescription.tenant_id == tenant_id,
                Prescription.patient_id == patient_id,
            )
            .order_by(Prescription.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
