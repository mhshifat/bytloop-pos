"""Shift service — open / close / variance."""

from __future__ import annotations

import pytest

from src.core.errors import ConflictError, NotFoundError
from src.modules.identity.entity import User
from src.modules.identity.repository import UserRepository
from src.modules.shifts.entity import ShiftStatus
from src.modules.shifts.service import ShiftService
from src.modules.tenants.repository import TenantRepository


async def _owner(db_session):  # type: ignore[no-untyped-def]
    tenant = await TenantRepository(db_session).create(
        slug="s1", name="S", country="BD", default_currency="BDT"
    )
    user = User(
        tenant_id=tenant.id,
        email="owner@ex.com",
        first_name="Own",
        last_name="Er",
        password_hash=None,
        email_verified=True,
        roles=["owner"],
        terms_accepted_at=None,
    )
    await UserRepository(db_session).add(user)
    return tenant, user


@pytest.mark.asyncio
async def test_open_then_close_records_variance(db_session):
    tenant, user = await _owner(db_session)
    service = ShiftService(db_session)

    shift = await service.open(
        tenant_id=tenant.id, cashier_id=user.id, opening_float_cents=10000
    )
    assert shift.status == ShiftStatus.OPEN

    closed = await service.close(
        tenant_id=tenant.id, cashier_id=user.id, closing_counted_cents=11000
    )
    assert closed.status == ShiftStatus.CLOSED
    # No cash sales in this test → expected == opening float (10000).
    assert closed.expected_cash_cents == 10000
    assert closed.variance_cents == 1000


@pytest.mark.asyncio
async def test_second_open_conflicts_while_one_is_open(db_session):
    tenant, user = await _owner(db_session)
    service = ShiftService(db_session)
    await service.open(tenant_id=tenant.id, cashier_id=user.id, opening_float_cents=0)
    with pytest.raises(ConflictError):
        await service.open(
            tenant_id=tenant.id, cashier_id=user.id, opening_float_cents=0
        )


@pytest.mark.asyncio
async def test_close_without_open_raises(db_session):
    tenant, user = await _owner(db_session)
    with pytest.raises(NotFoundError):
        await ShiftService(db_session).close(
            tenant_id=tenant.id, cashier_id=user.id, closing_counted_cents=0
        )
