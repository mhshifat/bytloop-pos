"""Grocery — PLU lookup + weighable pricing."""

from __future__ import annotations

import pytest

from src.core.errors import NotFoundError
from src.modules.catalog.entity import Product
from src.modules.catalog.repository import ProductRepository
from src.modules.tenants.repository import TenantRepository
from src.verticals.retail.grocery.entity import GrocerySku, PluCode, SellUnit
from src.verticals.retail.grocery.service import GroceryService


@pytest.mark.asyncio
async def test_plu_lookup_returns_product_id(db_session):
    tenant = await TenantRepository(db_session).create(
        slug="g1", name="G", country="BD", default_currency="BDT"
    )
    product = Product(
        tenant_id=tenant.id,
        sku="APPLE",
        barcode=None,
        name="Apple",
        description=None,
        category_id=None,
        price_cents=0,
        currency="BDT",
        is_active=True,
        track_inventory=False,
        tax_rate=0,  # type: ignore[arg-type]
        vertical_data={},
    )
    await ProductRepository(db_session).add(product)

    db_session.add(PluCode(tenant_id=tenant.id, code="4011", product_id=product.id))
    await db_session.flush()

    service = GroceryService(db_session)
    found = await service.lookup_by_plu(tenant_id=tenant.id, code="4011")
    assert found == product.id

    with pytest.raises(NotFoundError):
        await service.lookup_by_plu(tenant_id=tenant.id, code="0000")


@pytest.mark.asyncio
async def test_price_by_weight_applies_tare_and_unit(db_session):
    tenant = await TenantRepository(db_session).create(
        slug="g2", name="G", country="BD", default_currency="BDT"
    )
    product = Product(
        tenant_id=tenant.id,
        sku="BANANA",
        barcode=None,
        name="Banana",
        description=None,
        category_id=None,
        price_cents=0,
        currency="BDT",
        is_active=True,
        track_inventory=False,
        tax_rate=0,  # type: ignore[arg-type]
        vertical_data={},
    )
    await ProductRepository(db_session).add(product)

    db_session.add(
        GrocerySku(
            product_id=product.id,
            tenant_id=tenant.id,
            sell_unit=SellUnit.KG,
            price_per_unit_cents=10000,  # 100.00 per kg
            tare_grams=50,
        )
    )
    await db_session.flush()

    service = GroceryService(db_session)
    # 1050g gross - 50g tare = 1.0 kg * 10000 cents = 10000
    price = await service.price_by_weight(
        tenant_id=tenant.id, product_id=product.id, grams=1050
    )
    assert price == 10000
