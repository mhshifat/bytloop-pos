from __future__ import annotations

from datetime import date, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.specialty.pharmacy.schemas import (
    BatchCreate,
    BatchRead,
    DrugMetadataRead,
    DrugMetadataUpsert,
    FefoDispatchLine,
    FefoDispatchRequest,
    PrescriptionCreate,
    PrescriptionRead,
)
from src.verticals.specialty.pharmacy.service import PharmacyService

router = APIRouter(prefix="/pharmacy", tags=["pharmacy"])


@router.get(
    "/batches",
    response_model=list[BatchRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_batches(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    product_id: UUID | None = Query(default=None, alias="productId"),
) -> list[BatchRead]:
    rows = await PharmacyService(db).list_batches(
        tenant_id=user.tenant_id, product_id=product_id
    )
    return [BatchRead.model_validate(r) for r in rows]


@router.get(
    "/batches/expiring",
    response_model=list[BatchRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_expiring_batches(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    days: int = Query(default=30, ge=1, le=365),
) -> list[BatchRead]:
    before = date.today() + timedelta(days=days)
    rows = await PharmacyService(db).list_expiring(
        tenant_id=user.tenant_id, before=before
    )
    return [BatchRead.model_validate(r) for r in rows]


@router.post(
    "/batches",
    response_model=BatchRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def create_batch(
    data: BatchCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> BatchRead:
    batch = await PharmacyService(db).record_batch(
        tenant_id=user.tenant_id,
        product_id=data.product_id,
        batch_no=data.batch_no,
        expiry_date=data.expiry_date,
        quantity=data.quantity,
    )
    return BatchRead.model_validate(batch)


@router.put(
    "/drug-metadata",
    response_model=DrugMetadataRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def upsert_drug_metadata(
    data: DrugMetadataUpsert,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DrugMetadataRead:
    meta = await PharmacyService(db).upsert_metadata(
        tenant_id=user.tenant_id,
        product_id=data.product_id,
        is_controlled=data.is_controlled,
        schedule=data.schedule,
        dosage_form=data.dosage_form,
        strength=data.strength,
    )
    return DrugMetadataRead.model_validate(meta)


@router.post(
    "/prescriptions",
    response_model=PrescriptionRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def create_prescription(
    data: PrescriptionCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PrescriptionRead:
    rx = await PharmacyService(db).create_prescription(
        tenant_id=user.tenant_id,
        customer_id=data.customer_id,
        prescription_no=data.prescription_no,
        doctor_name=data.doctor_name,
        doctor_license=data.doctor_license,
        issued_on=data.issued_on,
        notes=data.notes,
    )
    return PrescriptionRead.model_validate(rx)


@router.get(
    "/prescriptions",
    response_model=list[PrescriptionRead],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def list_prescriptions(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    customer_id: UUID | None = Query(default=None, alias="customerId"),
) -> list[PrescriptionRead]:
    rows = await PharmacyService(db).list_prescriptions(
        tenant_id=user.tenant_id, customer_id=customer_id
    )
    return [PrescriptionRead.model_validate(r) for r in rows]


@router.post(
    "/fefo-dispatch",
    response_model=list[FefoDispatchLine],
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def fefo_dispatch(
    req: FefoDispatchRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[FefoDispatchLine]:
    """First-Expired-First-Out pull from batches. Gated by controlled-substance
    check — callers without a prescription for a scheduled drug get 403."""
    service = PharmacyService(db)
    await service.assert_dispensable(
        tenant_id=user.tenant_id,
        product_id=req.product_id,
        prescription_id=req.prescription_id,
    )
    taken = await service.dispatch_fefo(
        tenant_id=user.tenant_id, product_id=req.product_id, quantity=req.quantity
    )
    return [
        FefoDispatchLine(batch_id=b.id, batch_no=b.batch_no, quantity=qty)
        for b, qty in taken
    ]
