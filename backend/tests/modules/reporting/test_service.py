"""Reporting — dashboard, top products, payment breakdown over real orders."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.modules.catalog.entity import Product
from src.modules.catalog.repository import ProductRepository
from src.modules.reporting.service import ReportingService
from src.modules.sales.entity import OrderType, PaymentMethod
from src.modules.sales.schemas import CartItemInput
from src.modules.sales.service import SalesService
from src.modules.tenants.repository import TenantRepository


@pytest.fixture
async def seeded(db_session):  # type: ignore[no-untyped-def]
    tenant = await TenantRepository(db_session).create(
        slug="rep", name="Rep", country="BD", default_currency="BDT"
    )
    widget = Product(
        tenant_id=tenant.id,
        sku="RPT-1",
        barcode=None,
        name="Widget",
        description=None,
        category_id=None,
        price_cents=500,
        currency="BDT",
        is_active=True,
        track_inventory=False,
        tax_rate=Decimal("0"),
        vertical_data={},
    )
    gadget = Product(
        tenant_id=tenant.id,
        sku="RPT-2",
        barcode=None,
        name="Gadget",
        description=None,
        category_id=None,
        price_cents=1200,
        currency="BDT",
        is_active=True,
        track_inventory=False,
        tax_rate=Decimal("0"),
        vertical_data={},
    )
    repo = ProductRepository(db_session)
    await repo.add(widget)
    await repo.add(gadget)
    return tenant, widget, gadget


@pytest.mark.asyncio
async def test_top_products_ranks_by_revenue(db_session, seeded):
    tenant, widget, gadget = seeded
    sales = SalesService(db_session)

    # Widget: 3 × 500 = 1500
    await sales.checkout(
        tenant_id=tenant.id,
        cashier_id=tenant.id,
        items=[CartItemInput(product_id=widget.id, quantity=3)],
        order_type=OrderType.RETAIL,
        payment_method=PaymentMethod.CASH,
        amount_tendered_cents=1500,
    )
    # Gadget: 2 × 1200 = 2400
    await sales.checkout(
        tenant_id=tenant.id,
        cashier_id=tenant.id,
        items=[CartItemInput(product_id=gadget.id, quantity=2)],
        order_type=OrderType.RETAIL,
        payment_method=PaymentMethod.CASH,
        amount_tendered_cents=2400,
    )

    rows = await ReportingService(db_session).top_products(tenant_id=tenant.id, days=30)
    assert len(rows) == 2
    assert rows[0]["name"] == "Gadget"
    assert rows[0]["revenueCents"] == 2400
    assert rows[0]["unitsSold"] == 2
    assert rows[1]["name"] == "Widget"
    assert rows[1]["revenueCents"] == 1500


@pytest.mark.asyncio
async def test_top_products_respects_limit(db_session, seeded):
    tenant, widget, gadget = seeded
    sales = SalesService(db_session)
    await sales.checkout(
        tenant_id=tenant.id,
        cashier_id=tenant.id,
        items=[
            CartItemInput(product_id=widget.id, quantity=1),
            CartItemInput(product_id=gadget.id, quantity=1),
        ],
        order_type=OrderType.RETAIL,
        payment_method=PaymentMethod.CASH,
        amount_tendered_cents=1700,
    )

    rows = await ReportingService(db_session).top_products(
        tenant_id=tenant.id, days=30, limit=1
    )
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_payment_breakdown_sums_by_method(db_session, seeded):
    tenant, widget, _ = seeded
    sales = SalesService(db_session)

    await sales.checkout(
        tenant_id=tenant.id,
        cashier_id=tenant.id,
        items=[CartItemInput(product_id=widget.id, quantity=1)],
        order_type=OrderType.RETAIL,
        payment_method=PaymentMethod.CASH,
        amount_tendered_cents=500,
    )
    await sales.checkout(
        tenant_id=tenant.id,
        cashier_id=tenant.id,
        items=[CartItemInput(product_id=widget.id, quantity=2)],
        order_type=OrderType.RETAIL,
        payment_method=PaymentMethod.CASH,
        amount_tendered_cents=1000,
    )

    rows = await ReportingService(db_session).payment_method_breakdown(
        tenant_id=tenant.id, days=30
    )
    assert len(rows) == 1
    cash = rows[0]
    assert cash["method"] == "cash"
    assert cash["orderCount"] == 2
    assert cash["amountCents"] == 1500


@pytest.mark.asyncio
async def test_reports_isolate_by_tenant(db_session, seeded):
    tenant, widget, _ = seeded
    other = await TenantRepository(db_session).create(
        slug="other", name="Other", country="BD", default_currency="BDT"
    )
    sales = SalesService(db_session)

    await sales.checkout(
        tenant_id=tenant.id,
        cashier_id=tenant.id,
        items=[CartItemInput(product_id=widget.id, quantity=1)],
        order_type=OrderType.RETAIL,
        payment_method=PaymentMethod.CASH,
        amount_tendered_cents=500,
    )

    rows = await ReportingService(db_session).top_products(tenant_id=other.id, days=30)
    assert rows == []
    payments = await ReportingService(db_session).payment_method_breakdown(
        tenant_id=other.id, days=30
    )
    assert payments == []
