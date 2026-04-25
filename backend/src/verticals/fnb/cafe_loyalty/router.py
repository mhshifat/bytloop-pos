from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.fnb.cafe_loyalty.schemas import (
    IssueCardRequest,
    LoyaltyCardRead,
    PunchRequest,
    PunchResponse,
    RedeemRequest,
)
from src.verticals.fnb.cafe_loyalty.service import CafeLoyaltyService

router = APIRouter(prefix="/cafe-loyalty", tags=["cafe-loyalty"])


@router.get(
    "/cards",
    response_model=list[LoyaltyCardRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_cards_for_customer(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    customer_id: UUID = Query(..., alias="customerId"),
) -> list[LoyaltyCardRead]:
    rows = await CafeLoyaltyService(db).list_for_customer(
        tenant_id=user.tenant_id, customer_id=customer_id
    )
    return [LoyaltyCardRead.model_validate(r) for r in rows]


@router.post(
    "/cards",
    response_model=LoyaltyCardRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.PRODUCTS_WRITE))],
)
async def issue_card(
    req: IssueCardRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> LoyaltyCardRead:
    card = await CafeLoyaltyService(db).issue_card(
        tenant_id=user.tenant_id,
        customer_id=req.customer_id,
        card_code=req.card_code,
        punches_required=req.punches_required,
    )
    return LoyaltyCardRead.model_validate(card)


@router.post(
    "/punch",
    response_model=PunchResponse,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def punch_card(
    req: PunchRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> PunchResponse:
    card, earned = await CafeLoyaltyService(db).punch(
        tenant_id=user.tenant_id, card_code=req.card_code, count=req.count
    )
    return PunchResponse(
        card=LoyaltyCardRead.model_validate(card), earned_this_punch=earned
    )


@router.post(
    "/redeem",
    response_model=LoyaltyCardRead,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def redeem_free_item(
    req: RedeemRequest,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> LoyaltyCardRead:
    card = await CafeLoyaltyService(db).redeem_free_item(
        tenant_id=user.tenant_id, card_code=req.card_code
    )
    return LoyaltyCardRead.model_validate(card)
