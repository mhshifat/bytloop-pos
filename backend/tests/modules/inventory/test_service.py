"""Inventory service — manual_adjust, reorder point, transfer between locations."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.core.errors import ConflictError, ValidationError
from src.modules.catalog.entity import Product
from src.modules.catalog.repository import ProductRepository
from src.modules.inventory.service import InventoryService
from src.modules.tenants.repository import TenantRepository


@pytest.fixture
async def seeded(db_session):  # type: ignore[no-untyped-def]
    tenant = await TenantRepository(db_session).create(
        slug="inv", name="Inv", country="BD", default_currency="BDT"
    )
    product = Product(
        tenant_id=tenant.id,
        sku="INV-1",
        barcode=None,
        name="Widget",
        description=None,
        category_id=None,
        price_cents=0,
        currency="BDT",
        is_active=True,
        track_inventory=True,
        tax_rate=Decimal("0"),
        vertical_data={},
    )
    await ProductRepository(db_session).add(product)
    return tenant, product


@pytest.mark.asyncio
async def test_manual_adjust_positive_delta_receives_stock(seeded, db_session):
    tenant, product = seeded
    service = InventoryService(db_session)

    new_qty = await service.manual_adjust(
        tenant_id=tenant.id, product_id=product.id, delta=10
    )
    assert new_qty == 10

    location_id = await service.default_location_id(tenant_id=tenant.id)
    assert (
        await service.current_quantity(
            tenant_id=tenant.id, product_id=product.id, location_id=location_id
        )
        == 10
    )


@pytest.mark.asyncio
async def test_manual_adjust_negative_delta_removes_stock(seeded, db_session):
    tenant, product = seeded
    service = InventoryService(db_session)

    await service.manual_adjust(tenant_id=tenant.id, product_id=product.id, delta=20)
    new_qty = await service.manual_adjust(
        tenant_id=tenant.id, product_id=product.id, delta=-7
    )
    assert new_qty == 13


@pytest.mark.asyncio
async def test_set_reorder_point_creates_level_if_missing(seeded, db_session):
    tenant, product = seeded
    service = InventoryService(db_session)

    result = await service.set_reorder_point(
        tenant_id=tenant.id, product_id=product.id, reorder_point=5
    )
    assert result == 5

    updated = await service.set_reorder_point(
        tenant_id=tenant.id, product_id=product.id, reorder_point=12
    )
    assert updated == 12


@pytest.mark.asyncio
async def test_transfer_happy_path(seeded, db_session):
    tenant, product = seeded
    service = InventoryService(db_session)

    source_id = await service.default_location_id(tenant_id=tenant.id)
    destination = await service.create_location(
        tenant_id=tenant.id, code="shop", name="Shop"
    )
    await service.receive_stock(
        tenant_id=tenant.id,
        product_id=product.id,
        location_id=source_id,
        quantity=50,
    )

    source_qty, dest_qty = await service.transfer_stock(
        tenant_id=tenant.id,
        product_id=product.id,
        source_location_id=source_id,
        destination_location_id=destination.id,
        quantity=20,
    )
    assert source_qty == 30
    assert dest_qty == 20


@pytest.mark.asyncio
async def test_transfer_rejects_insufficient_stock(seeded, db_session):
    tenant, product = seeded
    service = InventoryService(db_session)
    source_id = await service.default_location_id(tenant_id=tenant.id)
    destination = await service.create_location(
        tenant_id=tenant.id, code="shop", name="Shop"
    )
    await service.receive_stock(
        tenant_id=tenant.id,
        product_id=product.id,
        location_id=source_id,
        quantity=5,
    )
    with pytest.raises(ConflictError):
        await service.transfer_stock(
            tenant_id=tenant.id,
            product_id=product.id,
            source_location_id=source_id,
            destination_location_id=destination.id,
            quantity=10,
        )


@pytest.mark.asyncio
async def test_transfer_rejects_same_location(seeded, db_session):
    tenant, product = seeded
    service = InventoryService(db_session)
    source_id = await service.default_location_id(tenant_id=tenant.id)
    await service.receive_stock(
        tenant_id=tenant.id,
        product_id=product.id,
        location_id=source_id,
        quantity=5,
    )
    with pytest.raises(ValidationError):
        await service.transfer_stock(
            tenant_id=tenant.id,
            product_id=product.id,
            source_location_id=source_id,
            destination_location_id=source_id,
            quantity=1,
        )


@pytest.mark.asyncio
async def test_transfer_rejects_non_positive_quantity(seeded, db_session):
    tenant, product = seeded
    service = InventoryService(db_session)
    source_id = await service.default_location_id(tenant_id=tenant.id)
    destination = await service.create_location(
        tenant_id=tenant.id, code="shop", name="Shop"
    )
    with pytest.raises(ValidationError):
        await service.transfer_stock(
            tenant_id=tenant.id,
            product_id=product.id,
            source_location_id=source_id,
            destination_location_id=destination.id,
            quantity=0,
        )
