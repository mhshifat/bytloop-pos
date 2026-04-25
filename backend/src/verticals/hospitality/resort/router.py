from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.hospitality.resort.schemas import (
    AmenitiesRead,
    AttachPackageRequest,
    ResortPackageBookingRead,
    ResortPackageCreate,
    ResortPackageRead,
)
from src.verticals.hospitality.resort.service import ResortService

router = APIRouter(prefix="/resort", tags=["resort"])


@router.get(
    "/packages",
    response_model=list[ResortPackageRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_packages(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[ResortPackageRead]:
    rows = await ResortService(db).list_packages(tenant_id=user.tenant_id)
    return [ResortPackageRead.model_validate(r) for r in rows]


@router.post(
    "/packages",
    response_model=ResortPackageRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def create_package(
    data: ResortPackageCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ResortPackageRead:
    package = await ResortService(db).create_package(
        tenant_id=user.tenant_id,
        code=data.code,
        name=data.name,
        per_night_price_cents=data.per_night_price_cents,
        includes_meals=data.includes_meals,
        includes_drinks=data.includes_drinks,
        includes_spa=data.includes_spa,
        includes_activities=data.includes_activities,
    )
    return ResortPackageRead.model_validate(package)


@router.post(
    "/reservations/{reservation_id}/package",
    response_model=ResortPackageBookingRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def attach_package(
    reservation_id: UUID,
    data: AttachPackageRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> ResortPackageBookingRead:
    booking = await ResortService(db).attach_to_reservation(
        tenant_id=user.tenant_id,
        reservation_id=reservation_id,
        package_code=data.package_code,
        nights=data.nights,
    )
    return ResortPackageBookingRead.model_validate(booking)


@router.get(
    "/reservations/{reservation_id}/amenities",
    response_model=AmenitiesRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def reservation_amenities(
    reservation_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> AmenitiesRead:
    booking, package = await ResortService(db).amenities_included(
        tenant_id=user.tenant_id, reservation_id=reservation_id
    )
    return AmenitiesRead(
        reservation_id=reservation_id,
        package_code=package.code,
        includes_meals=package.includes_meals,
        includes_drinks=package.includes_drinks,
        includes_spa=package.includes_spa,
        includes_activities=package.includes_activities,
    )
