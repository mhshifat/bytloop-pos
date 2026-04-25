from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import NotFoundError
from src.verticals.specialty.donations.entity import Campaign, Donation


class DonationsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Campaigns
    # ──────────────────────────────────────────────

    async def list_campaigns(self, *, tenant_id: UUID) -> list[Campaign]:
        stmt = (
            select(Campaign)
            .where(Campaign.tenant_id == tenant_id)
            .order_by(Campaign.code)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def create_campaign(
        self,
        *,
        tenant_id: UUID,
        code: str,
        name: str,
        goal_cents: int,
        starts_on,
        ends_on,
        active: bool,
    ) -> Campaign:
        campaign = Campaign(
            tenant_id=tenant_id,
            code=code,
            name=name,
            goal_cents=goal_cents,
            starts_on=starts_on,
            ends_on=ends_on,
            active=active,
        )
        self._session.add(campaign)
        await self._session.flush()
        return campaign

    # ──────────────────────────────────────────────
    # Donations
    # ──────────────────────────────────────────────

    async def list_donations(
        self, *, tenant_id: UUID, campaign: str | None = None
    ) -> list[Donation]:
        stmt = select(Donation).where(Donation.tenant_id == tenant_id)
        if campaign is not None:
            stmt = stmt.where(Donation.campaign == campaign)
        stmt = stmt.order_by(Donation.received_at.desc())
        return list((await self._session.execute(stmt)).scalars().all())

    async def get_donation(
        self, *, tenant_id: UUID, donation_id: UUID
    ) -> Donation:
        donation = await self._session.get(Donation, donation_id)
        if donation is None or donation.tenant_id != tenant_id:
            raise NotFoundError("Donation not found.")
        return donation

    async def _next_receipt_no(self, *, tenant_id: UUID) -> str:
        """Sequential per-tenant receipt number: RCPT-<padded count+1>.

        Using COUNT keeps gaps away from the regulator — every row a tenant
        has filed is part of the sequence. For very large tenants we'd swap
        this for a dedicated counter table with SELECT ... FOR UPDATE.
        """
        stmt = (
            select(func.count())
            .select_from(Donation)
            .where(Donation.tenant_id == tenant_id)
        )
        count = int((await self._session.execute(stmt)).scalar_one())
        return f"RCPT-{count + 1:07d}"

    async def create_donation(
        self,
        *,
        tenant_id: UUID,
        customer_id: UUID | None,
        amount_cents: int,
        currency: str,
        campaign: str | None,
        donor_name_override: str | None,
        is_anonymous: bool,
        tax_deductible: bool,
    ) -> Donation:
        receipt_no = await self._next_receipt_no(tenant_id=tenant_id)
        donation = Donation(
            tenant_id=tenant_id,
            customer_id=customer_id,
            amount_cents=amount_cents,
            currency=currency,
            campaign=campaign,
            donor_name_override=donor_name_override,
            is_anonymous=is_anonymous,
            tax_deductible=tax_deductible,
            receipt_no=receipt_no,
        )
        self._session.add(donation)
        await self._session.flush()
        return donation

    # ──────────────────────────────────────────────
    # Reporting
    # ──────────────────────────────────────────────

    async def list_campaign_totals(
        self, *, tenant_id: UUID, campaign_code: str
    ) -> dict:
        totals_stmt = select(
            func.count(Donation.id),
            func.coalesce(func.sum(Donation.amount_cents), 0),
        ).where(
            Donation.tenant_id == tenant_id,
            Donation.campaign == campaign_code,
        )
        count, total = (await self._session.execute(totals_stmt)).one()

        goal_stmt = select(Campaign).where(
            Campaign.tenant_id == tenant_id,
            Campaign.code == campaign_code,
        )
        campaign = (await self._session.execute(goal_stmt)).scalar_one_or_none()
        goal = campaign.goal_cents if campaign is not None else 0

        progress = (float(total) / float(goal) * 100.0) if goal > 0 else 0.0
        return {
            "code": campaign_code,
            "donation_count": int(count or 0),
            "total_cents": int(total or 0),
            "goal_cents": int(goal),
            "progress_pct": round(progress, 2),
        }

    async def issue_receipt(
        self, *, tenant_id: UUID, donation_id: UUID
    ) -> dict:
        """Build a printable receipt payload for the given donation."""
        donation = await self.get_donation(
            tenant_id=tenant_id, donation_id=donation_id
        )
        donor_name = (
            "Anonymous"
            if donation.is_anonymous
            else (donation.donor_name_override or "")
        )
        return {
            "receipt_no": donation.receipt_no,
            "donor_name": donor_name,
            "amount_cents": donation.amount_cents,
            "currency": donation.currency,
            "campaign": donation.campaign,
            "tax_deductible": donation.tax_deductible,
            "received_at": donation.received_at,
        }
