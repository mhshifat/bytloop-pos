"""Discount resolution — percent and fixed."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.core.errors import NotFoundError
from src.modules.discounts.schemas import DiscountCreate
from src.modules.discounts.service import DiscountService
from src.modules.tenants.repository import TenantRepository


@pytest.mark.asyncio
async def test_percent_discount_applies_to_subtotal(db_session):
    tenant = await TenantRepository(db_session).create(
        slug="d1", name="D", country="BD", default_currency="BDT"
    )
    service = DiscountService(db_session)
    await service.create(
        tenant_id=tenant.id,
        data=DiscountCreate(
            code="TENOFF",
            name="10% off",
            kind="percent",
            percent=Decimal("0.10"),
        ),
    )

    amount = await service.resolve(
        tenant_id=tenant.id, code="TENOFF", subtotal_cents=10000
    )
    assert amount == 1000


@pytest.mark.asyncio
async def test_fixed_discount_capped_at_subtotal(db_session):
    tenant = await TenantRepository(db_session).create(
        slug="d2", name="D", country="BD", default_currency="BDT"
    )
    service = DiscountService(db_session)
    await service.create(
        tenant_id=tenant.id,
        data=DiscountCreate(
            code="BIG",
            name="BDT 500 off",
            kind="fixed",
            amount_cents=50000,
        ),
    )

    # Subtotal smaller than discount → caps at subtotal.
    amount = await service.resolve(tenant_id=tenant.id, code="BIG", subtotal_cents=10000)
    assert amount == 10000


@pytest.mark.asyncio
async def test_unknown_code_raises_not_found(db_session):
    tenant = await TenantRepository(db_session).create(
        slug="d3", name="D", country="BD", default_currency="BDT"
    )
    with pytest.raises(NotFoundError):
        await DiscountService(db_session).resolve(
            tenant_id=tenant.id, code="NOPE", subtotal_cents=500
        )
