from __future__ import annotations

from fastapi import APIRouter, Depends, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.modules.discounts.schemas import DiscountCreate, DiscountRead
from src.modules.discounts.service import DiscountService

router = APIRouter(prefix="/discounts", tags=["discounts"])


@router.get("", response_model=list[DiscountRead], dependencies=[Depends(requires(Permission.PRODUCTS_READ))])
async def list_discounts(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[DiscountRead]:
    rows = await DiscountService(db).list_active(tenant_id=user.tenant_id)
    return [DiscountRead.model_validate(d) for d in rows]


@router.post(
    "",
    response_model=DiscountRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def create_discount(
    data: DiscountCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DiscountRead:
    discount = await DiscountService(db).create(tenant_id=user.tenant_id, data=data)
    return DiscountRead.model_validate(discount)
