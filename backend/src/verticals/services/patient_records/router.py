from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.services.patient_records.schemas import (
    PatientCreate,
    PatientRead,
    PrescriptionCreate,
    PrescriptionRead,
    VisitCreate,
    VisitRead,
)
from src.verticals.services.patient_records.service import PatientRecordsService

router = APIRouter(prefix="/patient-records", tags=["patient-records"])


@router.get(
    "/patients",
    response_model=list[PatientRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_patients(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    search: str | None = Query(default=None),
) -> list[PatientRead]:
    rows = await PatientRecordsService(db).list_patients(
        tenant_id=user.tenant_id, search=search
    )
    return [PatientRead.model_validate(r) for r in rows]


@router.get(
    "/patients/{patient_id}",
    response_model=PatientRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def get_patient(
    patient_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PatientRead:
    patient = await PatientRecordsService(db).get_patient(
        tenant_id=user.tenant_id, patient_id=patient_id
    )
    return PatientRead.model_validate(patient)


@router.post(
    "/patients",
    response_model=PatientRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def register_patient(
    data: PatientCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PatientRead:
    patient = await PatientRecordsService(db).register_patient(
        tenant_id=user.tenant_id,
        customer_id=data.customer_id,
        kind=data.kind,
        first_name=data.first_name,
        pet_name=data.pet_name,
        dob_or_birth_year=data.dob_or_birth_year,
        species=data.species,
        breed=data.breed,
        allergies=data.allergies,
        notes=data.notes,
    )
    return PatientRead.model_validate(patient)


@router.post(
    "/visits",
    response_model=VisitRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def create_visit(
    data: VisitCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> VisitRead:
    visit = await PatientRecordsService(db).create_visit(
        tenant_id=user.tenant_id,
        patient_id=data.patient_id,
        attending_user_id=data.attending_user_id or user.id,
        visit_date=data.visit_date,
        chief_complaint=data.chief_complaint,
        diagnosis=data.diagnosis,
        treatment_notes=data.treatment_notes,
        order_id=data.order_id,
        follow_up_on=data.follow_up_on,
    )
    return VisitRead.model_validate(visit)


@router.get(
    "/patients/{patient_id}/visits",
    response_model=list[VisitRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def visit_history(
    patient_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[VisitRead]:
    rows = await PatientRecordsService(db).visit_history(
        tenant_id=user.tenant_id, patient_id=patient_id
    )
    return [VisitRead.model_validate(r) for r in rows]


@router.post(
    "/prescriptions",
    response_model=PrescriptionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def add_prescription(
    data: PrescriptionCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PrescriptionRead:
    rx = await PatientRecordsService(db).add_prescription(
        tenant_id=user.tenant_id,
        patient_id=data.patient_id,
        visit_id=data.visit_id,
        medication_name=data.medication_name,
        dosage=data.dosage,
        frequency=data.frequency,
        duration_days=data.duration_days,
        prescribed_by_user_id=user.id,
    )
    return PrescriptionRead.model_validate(rx)


@router.get(
    "/patients/{patient_id}/prescriptions",
    response_model=list[PrescriptionRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_prescriptions(
    patient_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[PrescriptionRead]:
    rows = await PatientRecordsService(db).list_prescriptions(
        tenant_id=user.tenant_id, patient_id=patient_id
    )
    return [PrescriptionRead.model_validate(r) for r in rows]
