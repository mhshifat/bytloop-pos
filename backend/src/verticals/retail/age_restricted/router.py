from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.retail.age_restricted.schemas import (
    AgeRestrictedProductRead,
    AgeVerificationLogRead,
    RequiresVerificationItem,
    RequiresVerificationRequest,
    SetMinAgeRequest,
    VerifyRequest,
)
from src.verticals.retail.age_restricted.service import AgeRestrictedService

router = APIRouter(prefix="/age-restricted", tags=["age-restricted"])


@router.put(
    "/products",
    response_model=AgeRestrictedProductRead,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def upsert_min_age(
    req: SetMinAgeRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> AgeRestrictedProductRead:
    rule = await AgeRestrictedService(db).set_min_age(
        tenant_id=user.tenant_id,
        product_id=req.product_id,
        min_age_years=req.min_age_years,
    )
    return AgeRestrictedProductRead.model_validate(rule)


@router.post(
    "/requires-verification",
    response_model=list[RequiresVerificationItem],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def requires_verification(
    req: RequiresVerificationRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[RequiresVerificationItem]:
    items = await AgeRestrictedService(db).requires_verification(
        tenant_id=user.tenant_id, product_ids=req.product_ids
    )
    return [RequiresVerificationItem(**row) for row in items]


@router.post(
    "/verify",
    response_model=AgeVerificationLogRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def verify(
    req: VerifyRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> AgeVerificationLogRead:
    log = await AgeRestrictedService(db).record_verification(
        tenant_id=user.tenant_id,
        order_id=req.order_id,
        customer_dob=req.customer_dob,
        verified_by_user_id=req.verified_by_user_id,
    )
    return AgeVerificationLogRead.model_validate(log)
