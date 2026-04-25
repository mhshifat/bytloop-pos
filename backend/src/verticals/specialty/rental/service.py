from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.verticals.specialty.rental.entity import (
    RentalAsset,
    RentalContract,
    RentalStatus,
)


@dataclass(frozen=True, slots=True)
class ReturnSummary:
    base_rental_cents: int
    late_fee_cents: int
    damage_fee_cents: int
    deposit_refund_cents: int
    net_due_cents: int


class RentalService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_assets(self, *, tenant_id: UUID) -> list[RentalAsset]:
        stmt = (
            select(RentalAsset)
            .where(RentalAsset.tenant_id == tenant_id)
            .order_by(RentalAsset.code)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def available_assets(
        self, *, tenant_id: UUID, starts_at: datetime, ends_at: datetime
    ) -> list[RentalAsset]:
        """Assets with no RESERVED/OUT contract overlapping the window."""
        if ends_at <= starts_at:
            raise ConflictError("End must be after start.")
        busy_subq = (
            select(RentalContract.asset_id)
            .where(
                RentalContract.tenant_id == tenant_id,
                RentalContract.status.in_([RentalStatus.RESERVED, RentalStatus.OUT]),
                RentalContract.starts_at < ends_at,
                RentalContract.ends_at > starts_at,
            )
        )
        stmt = (
            select(RentalAsset)
            .where(
                RentalAsset.tenant_id == tenant_id,
                RentalAsset.id.notin_(busy_subq),
            )
            .order_by(RentalAsset.code)
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def list_contracts(self, *, tenant_id: UUID) -> list[RentalContract]:
        stmt = (
            select(RentalContract)
            .where(RentalContract.tenant_id == tenant_id)
            .order_by(RentalContract.starts_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def add_asset(
        self,
        *,
        tenant_id: UUID,
        code: str,
        label: str,
        hourly_rate_cents: int,
        daily_rate_cents: int,
    ) -> RentalAsset:
        asset = RentalAsset(
            tenant_id=tenant_id,
            code=code,
            label=label,
            hourly_rate_cents=hourly_rate_cents,
            daily_rate_cents=daily_rate_cents,
        )
        self._session.add(asset)
        await self._session.flush()
        return asset

    async def reserve(
        self,
        *,
        tenant_id: UUID,
        asset_id: UUID,
        customer_id: UUID,
        starts_at: datetime,
        ends_at: datetime,
        deposit_cents: int,
    ) -> RentalContract:
        if ends_at <= starts_at:
            raise ConflictError("End must be after start.")
        clash_stmt = select(RentalContract).where(
            RentalContract.tenant_id == tenant_id,
            RentalContract.asset_id == asset_id,
            RentalContract.status.in_([RentalStatus.RESERVED, RentalStatus.OUT]),
            or_(
                and_(
                    RentalContract.starts_at <= starts_at,
                    RentalContract.ends_at > starts_at,
                ),
                and_(
                    RentalContract.starts_at < ends_at,
                    RentalContract.ends_at >= ends_at,
                ),
            ),
        )
        clash = (await self._session.execute(clash_stmt)).scalar_one_or_none()
        if clash is not None:
            raise ConflictError("Asset is already booked in that window.")

        contract = RentalContract(
            tenant_id=tenant_id,
            asset_id=asset_id,
            customer_id=customer_id,
            status=RentalStatus.RESERVED,
            starts_at=starts_at,
            ends_at=ends_at,
            returned_at=None,
            deposit_cents=deposit_cents,
            late_fee_cents=0,
            damage_fee_cents=0,
            damage_notes=None,
        )
        self._session.add(contract)
        await self._session.flush()
        return contract

    async def mark_out(
        self, *, tenant_id: UUID, contract_id: UUID
    ) -> RentalContract:
        """Handover to customer — contract transitions to OUT."""
        contract = await self._session.get(RentalContract, contract_id)
        if contract is None or contract.tenant_id != tenant_id:
            raise NotFoundError("Contract not found.")
        if contract.status != RentalStatus.RESERVED:
            raise ConflictError(
                f"Cannot check out a {contract.status.value} contract."
            )
        contract.status = RentalStatus.OUT
        await self._session.flush()
        return contract

    @staticmethod
    def _rental_cost(
        asset: RentalAsset, starts_at: datetime, billable_end: datetime
    ) -> int:
        """Daily rate × days, plus hourly for any partial trailing day."""
        if billable_end <= starts_at:
            return 0
        delta = billable_end - starts_at
        full_days = delta.days
        leftover_hours = delta.seconds // 3600
        if leftover_hours * asset.hourly_rate_cents > asset.daily_rate_cents:
            # Another day is cheaper billed as a full day
            full_days += 1
            leftover_hours = 0
        return (
            full_days * asset.daily_rate_cents
            + leftover_hours * asset.hourly_rate_cents
        )

    async def process_return(
        self,
        *,
        tenant_id: UUID,
        contract_id: UUID,
        returned_at: datetime | None = None,
        damage_fee_cents: int = 0,
        damage_notes: str | None = None,
    ) -> tuple[RentalContract, ReturnSummary]:
        """Close out a contract. Late fees computed from asset's own rates.

        If returned after ``ends_at``, charge the same rate for the overage
        (daily + hourly) rather than a flat penalty — customers hate surprise
        fees, operators want a predictable formula.
        """
        contract = await self._session.get(RentalContract, contract_id)
        if contract is None or contract.tenant_id != tenant_id:
            raise NotFoundError("Contract not found.")
        if contract.status == RentalStatus.RETURNED:
            raise ConflictError("Contract already returned.")

        asset = await self._session.get(RentalAsset, contract.asset_id)
        if asset is None:
            raise NotFoundError("Asset not found.")

        now = returned_at or datetime.now(tz=UTC)
        base = self._rental_cost(asset, contract.starts_at, contract.ends_at)
        late_fee = 0
        if now > contract.ends_at:
            late_fee = self._rental_cost(asset, contract.ends_at, now)

        contract.status = RentalStatus.RETURNED
        contract.returned_at = now
        contract.late_fee_cents = late_fee
        contract.damage_fee_cents = damage_fee_cents
        contract.damage_notes = damage_notes
        await self._session.flush()

        fees = late_fee + damage_fee_cents
        # Deposit first absorbs damage+late; refund any leftover; charge the rest
        deposit_applied = min(contract.deposit_cents, fees)
        deposit_refund = contract.deposit_cents - deposit_applied
        net_due = base + fees - deposit_applied

        summary = ReturnSummary(
            base_rental_cents=base,
            late_fee_cents=late_fee,
            damage_fee_cents=damage_fee_cents,
            deposit_refund_cents=deposit_refund,
            net_due_cents=net_due,
        )
        return contract, summary

    # Backwards-compat: `mark_returned` kept for callers that just want to
    # flip status without fee computation.
    async def mark_returned(
        self, *, tenant_id: UUID, contract_id: UUID
    ) -> RentalContract:
        contract, _ = await self.process_return(
            tenant_id=tenant_id, contract_id=contract_id
        )
        return contract
