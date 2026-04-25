from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.errors import ConflictError, NotFoundError
from src.verticals.services.rfid_memberships.entity import (
    PassStatus,
    PassUse,
    RfidPass,
)


class RedeemOutcome:
    __slots__ = ("success", "reason", "pass_id", "balance_uses_remaining")

    def __init__(
        self,
        *,
        success: bool,
        reason: str | None = None,
        pass_id: UUID | None = None,
        balance_uses_remaining: int | None = None,
    ) -> None:
        self.success = success
        self.reason = reason
        self.pass_id = pass_id
        self.balance_uses_remaining = balance_uses_remaining


class RfidMembershipsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # ──────────────────────────────────────────────
    # Pass lifecycle
    # ──────────────────────────────────────────────

    async def list_passes(self, *, tenant_id: UUID) -> list[RfidPass]:
        stmt = (
            select(RfidPass)
            .where(RfidPass.tenant_id == tenant_id)
            .order_by(RfidPass.created_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())

    async def issue_pass(
        self,
        *,
        tenant_id: UUID,
        rfid_tag: str,
        customer_id: UUID | None,
        plan_code: str,
        balance_uses: int | None = None,
        expires_on: date | None = None,
    ) -> RfidPass:
        existing_stmt = select(RfidPass).where(
            RfidPass.tenant_id == tenant_id,
            RfidPass.rfid_tag == rfid_tag,
        )
        if (await self._session.execute(existing_stmt)).scalar_one_or_none() is not None:
            raise ConflictError("That RFID tag is already issued.")

        pass_ = RfidPass(
            tenant_id=tenant_id,
            rfid_tag=rfid_tag,
            customer_id=customer_id,
            plan_code=plan_code,
            balance_uses=balance_uses,
            expires_on=expires_on,
            status=PassStatus.ACTIVE,
        )
        self._session.add(pass_)
        await self._session.flush()
        return pass_

    async def update_status(
        self, *, tenant_id: UUID, pass_id: UUID, status: PassStatus
    ) -> RfidPass:
        pass_ = await self._session.get(RfidPass, pass_id)
        if pass_ is None or pass_.tenant_id != tenant_id:
            raise NotFoundError("Pass not found.")
        pass_.status = status
        await self._session.flush()
        return pass_

    # ──────────────────────────────────────────────
    # Redemption
    # ──────────────────────────────────────────────

    async def redeem(
        self, *, tenant_id: UUID, rfid_tag: str, location: str = ""
    ) -> RedeemOutcome:
        stmt = select(RfidPass).where(
            RfidPass.tenant_id == tenant_id,
            RfidPass.rfid_tag == rfid_tag,
        )
        pass_ = (await self._session.execute(stmt)).scalar_one_or_none()
        if pass_ is None:
            return RedeemOutcome(success=False, reason="pass_not_found")

        if pass_.status == PassStatus.SUSPENDED:
            return RedeemOutcome(
                success=False, reason="pass_suspended", pass_id=pass_.id
            )
        if pass_.status == PassStatus.EXPIRED:
            return RedeemOutcome(
                success=False, reason="pass_expired", pass_id=pass_.id
            )

        # Time-based expiry takes precedence — a pass can be both "N uses
        # within D days"; either exhaustion expires it.
        if pass_.expires_on is not None and pass_.expires_on < date.today():
            pass_.status = PassStatus.EXPIRED
            await self._session.flush()
            return RedeemOutcome(
                success=False, reason="pass_expired", pass_id=pass_.id
            )

        if pass_.balance_uses is not None:
            if pass_.balance_uses <= 0:
                pass_.status = PassStatus.EXPIRED
                await self._session.flush()
                return RedeemOutcome(
                    success=False, reason="no_uses_remaining", pass_id=pass_.id
                )
            pass_.balance_uses -= 1
            if pass_.balance_uses == 0 and pass_.expires_on is None:
                # Punch card fully used — mark expired so future scans fail
                # cleanly without extra checks.
                pass_.status = PassStatus.EXPIRED

        self._session.add(
            PassUse(
                tenant_id=tenant_id,
                pass_id=pass_.id,
                location=location,
            )
        )
        await self._session.flush()
        return RedeemOutcome(
            success=True,
            pass_id=pass_.id,
            balance_uses_remaining=pass_.balance_uses,
        )

    async def transactions_for_pass(
        self, *, tenant_id: UUID, pass_id: UUID
    ) -> list[PassUse]:
        # Validate the pass belongs to the caller's tenant before leaking logs.
        pass_ = await self._session.get(RfidPass, pass_id)
        if pass_ is None or pass_.tenant_id != tenant_id:
            raise NotFoundError("Pass not found.")
        stmt = (
            select(PassUse)
            .where(PassUse.tenant_id == tenant_id, PassUse.pass_id == pass_id)
            .order_by(PassUse.used_at.desc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
