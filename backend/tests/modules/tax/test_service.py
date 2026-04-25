"""Tax rules — list + create."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.modules.tax.schemas import TaxRuleCreate
from src.modules.tax.service import TaxService
from src.modules.tenants.repository import TenantRepository


@pytest.mark.asyncio
async def test_create_then_list_active(db_session):
    tenant = await TenantRepository(db_session).create(
        slug="t1", name="T", country="BD", default_currency="BDT"
    )
    service = TaxService(db_session)

    await service.create(
        tenant_id=tenant.id,
        data=TaxRuleCreate(code="vat15", name="VAT 15", rate=Decimal("0.15")),
    )
    await service.create(
        tenant_id=tenant.id,
        data=TaxRuleCreate(
            code="sd05",
            name="SD 5",
            rate=Decimal("0.05"),
            is_inclusive=True,
        ),
    )

    rows = await service.list_active(tenant_id=tenant.id)
    codes = [r.code for r in rows]
    assert "VAT15" in codes
    assert "SD05" in codes
