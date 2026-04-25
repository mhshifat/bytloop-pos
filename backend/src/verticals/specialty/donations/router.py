from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from src.core.deps import DbSession, get_current_user, requires
from src.core.permissions import Permission
from src.verticals.specialty.donations.schemas import (
    CampaignCreate,
    CampaignRead,
    CampaignTotals,
    DonationCreate,
    DonationRead,
    DonationReceipt,
)
from src.verticals.specialty.donations.service import DonationsService

router = APIRouter(prefix="/donations", tags=["donations"])


@router.get(
    "/campaigns",
    response_model=list[CampaignRead],
    dependencies=[Depends(requires(Permission.PRODUCTS_READ))],
)
async def list_campaigns(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> list[CampaignRead]:
    rows = await DonationsService(db).list_campaigns(tenant_id=user.tenant_id)
    return [CampaignRead.model_validate(r) for r in rows]


@router.post(
    "/campaigns",
    response_model=CampaignRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.SETTINGS_MANAGE))],
)
async def create_campaign(
    data: CampaignCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CampaignRead:
    campaign = await DonationsService(db).create_campaign(
        tenant_id=user.tenant_id,
        code=data.code,
        name=data.name,
        goal_cents=data.goal_cents,
        starts_on=data.starts_on,
        ends_on=data.ends_on,
        active=data.active,
    )
    return CampaignRead.model_validate(campaign)


@router.get(
    "",
    response_model=list[DonationRead],
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def list_donations(
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
    campaign: str | None = Query(default=None),
) -> list[DonationRead]:
    rows = await DonationsService(db).list_donations(
        tenant_id=user.tenant_id, campaign=campaign
    )
    return [DonationRead.model_validate(r) for r in rows]


@router.post(
    "",
    response_model=DonationRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requires(Permission.ORDERS_CREATE))],
)
async def create_donation(
    data: DonationCreate,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DonationRead:
    donation = await DonationsService(db).create_donation(
        tenant_id=user.tenant_id,
        customer_id=data.customer_id,
        amount_cents=data.amount_cents,
        currency=data.currency,
        campaign=data.campaign,
        donor_name_override=data.donor_name_override,
        is_anonymous=data.is_anonymous,
        tax_deductible=data.tax_deductible,
    )
    return DonationRead.model_validate(donation)


@router.get(
    "/{donation_id}",
    response_model=DonationRead,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def get_donation(
    donation_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DonationRead:
    donation = await DonationsService(db).get_donation(
        tenant_id=user.tenant_id, donation_id=donation_id
    )
    return DonationRead.model_validate(donation)


@router.get(
    "/{donation_id}/receipt",
    response_model=DonationReceipt,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def issue_receipt(
    donation_id: UUID,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> DonationReceipt:
    receipt = await DonationsService(db).issue_receipt(
        tenant_id=user.tenant_id, donation_id=donation_id
    )
    return DonationReceipt(
        receipt_no=receipt["receipt_no"],
        donor_name=receipt["donor_name"],
        amount_cents=receipt["amount_cents"],
        currency=receipt["currency"],
        campaign=receipt["campaign"],
        tax_deductible=receipt["tax_deductible"],
        received_at=receipt["received_at"],
    )


@router.get(
    "/campaigns/{code}/totals",
    response_model=CampaignTotals,
    dependencies=[Depends(requires(Permission.REPORTS_VIEW))],
)
async def campaign_totals(
    code: str,
    db: DbSession,
    user=Depends(get_current_user),  # type: ignore[no-untyped-def]
) -> CampaignTotals:
    totals = await DonationsService(db).list_campaign_totals(
        tenant_id=user.tenant_id, campaign_code=code
    )
    return CampaignTotals(
        code=totals["code"],
        donation_count=totals["donation_count"],
        total_cents=totals["total_cents"],
        goal_cents=totals["goal_cents"],
        progress_pct=totals["progress_pct"],
    )
