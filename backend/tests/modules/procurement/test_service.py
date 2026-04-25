"""Procurement — supplier create → PO create → receive updates inventory."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.modules.catalog.entity import Product
from src.modules.catalog.repository import ProductRepository
from src.modules.inventory.api import InventoryService
from src.modules.procurement.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderItemInput,
    ReceiveItemInput,
    SupplierCreate,
)
from src.modules.procurement.service import ProcurementService
from src.modules.tenants.repository import TenantRepository


@pytest.fixture
async def seeded(db_session):  # type: ignore[no-untyped-def]
    tenant = await TenantRepository(db_session).create(
        slug="proc", name="Proc", country="BD", default_currency="BDT"
    )
    product = Product(
        tenant_id=tenant.id,
        sku="PT-1",
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
async def test_happy_path_po_receive_updates_inventory(seeded, db_session):
    tenant, product = seeded
    service = ProcurementService(db_session)

    supplier = await service.create_supplier(
        tenant_id=tenant.id,
        actor_id=None,
        data=SupplierCreate(code="ACME", name="Acme Widgets"),
    )
    po, items = await service.create_purchase_order(
        tenant_id=tenant.id,
        actor_id=None,
        data=PurchaseOrderCreate(
            supplier_id=supplier.id,
            currency="BDT",
            items=[
                PurchaseOrderItemInput(
                    product_id=product.id,
                    quantity_ordered=5,
                    unit_cost_cents=100,
                ),
            ],
        ),
    )
    assert po.total_cents == 500
    assert len(items) == 1

    # Receive 3 of 5
    await service.receive(
        tenant_id=tenant.id,
        actor_id=None,
        purchase_order_id=po.id,
        received=[ReceiveItemInput(item_id=items[0].id, quantity=3)],
    )

    inventory = InventoryService(db_session)
    location_id = await inventory.default_location_id(tenant_id=tenant.id)
    qty = await inventory.current_quantity(
        tenant_id=tenant.id, product_id=product.id, location_id=location_id
    )
    assert qty == 3

    # Receive remaining 2 — PO should close
    _, items_after = await service.get_purchase_order(
        tenant_id=tenant.id, purchase_order_id=po.id
    )
    await service.receive(
        tenant_id=tenant.id,
        actor_id=None,
        purchase_order_id=po.id,
        received=[ReceiveItemInput(item_id=items_after[0].id, quantity=2)],
    )
    final_qty = await inventory.current_quantity(
        tenant_id=tenant.id, product_id=product.id, location_id=location_id
    )
    assert final_qty == 5
