"""Cash-checkout happy path for the sales service."""

from __future__ import annotations

import pytest
from decimal import Decimal

from src.core.errors import ValidationError
from src.modules.catalog.entity import Product
from src.modules.catalog.repository import ProductRepository
from src.modules.sales.entity import OrderStatus, OrderType, PaymentMethod
from src.modules.sales.schemas import CartItemInput
from src.modules.sales.service import SalesService
from src.modules.tenants.repository import TenantRepository


@pytest.fixture
async def seeded_tenant_and_product(db_session):  # type: ignore[no-untyped-def]
    tenant = await TenantRepository(db_session).create(
        slug="acme", name="Acme", country="BD", default_currency="BDT"
    )
    product = Product(
        tenant_id=tenant.id,
        sku="SKU-1",
        barcode=None,
        name="Test product",
        description=None,
        category_id=None,
        price_cents=1000,
        currency="BDT",
        is_active=True,
        track_inventory=False,
        tax_rate=Decimal("0"),
        vertical_data={},
    )
    await ProductRepository(db_session).add(product)
    return tenant, product


@pytest.mark.asyncio
async def test_cash_checkout_creates_order_and_payment(db_session, seeded_tenant_and_product):
    tenant, product = seeded_tenant_and_product
    service = SalesService(db_session)

    sale = await service.checkout(
        tenant_id=tenant.id,
        cashier_id=tenant.id,  # doubles as placeholder user id for the cashier FK
        items=[CartItemInput(product_id=product.id, quantity=2)],
        order_type=OrderType.RETAIL,
        payment_method=PaymentMethod.CASH,
        amount_tendered_cents=2500,
    )

    assert sale.order.status == OrderStatus.COMPLETED
    assert sale.order.total_cents == 2000
    assert sale.change_due_cents == 500
    assert len(sale.items) == 1
    assert len(sale.payments) == 1


@pytest.mark.asyncio
async def test_insufficient_tender_is_rejected(db_session, seeded_tenant_and_product):
    tenant, product = seeded_tenant_and_product
    service = SalesService(db_session)

    with pytest.raises(ValidationError):
        await service.checkout(
            tenant_id=tenant.id,
            cashier_id=tenant.id,
            items=[CartItemInput(product_id=product.id, quantity=1)],
            order_type=OrderType.RETAIL,
            payment_method=PaymentMethod.CASH,
            amount_tendered_cents=100,
        )
