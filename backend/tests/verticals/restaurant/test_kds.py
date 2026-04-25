"""Tests for restaurant KOT fire + KDS transitions."""

from __future__ import annotations

import pytest

from src.modules.catalog.entity import Product
from src.modules.catalog.repository import ProductRepository
from src.modules.inventory.repository import LocationRepository
from src.modules.sales.entity import Order, OrderStatus, OrderType
from src.modules.sales.repository import OrderRepository
from src.modules.tenants.repository import TenantRepository
from src.verticals.fnb.restaurant.entity import KdsStation, KotStatus
from src.verticals.fnb.restaurant.schemas import KotItemInput
from src.verticals.fnb.restaurant.service import RestaurantService


@pytest.mark.asyncio
async def test_fire_kot_creates_ticket_and_items(db_session, monkeypatch):
    # publish() hits Redis — stub it out for unit test isolation
    from src.verticals.fnb.restaurant import service as svc_mod

    async def _noop_publish(*_args, **_kwargs):  # type: ignore[no-untyped-def]
        return None

    monkeypatch.setattr(svc_mod, "publish", _noop_publish)

    tenant = await TenantRepository(db_session).create(
        slug="rx", name="R", country="BD", default_currency="BDT"
    )
    location = await LocationRepository(db_session).default_for_tenant(tenant.id)
    order = Order(
        tenant_id=tenant.id,
        location_id=location.id,
        cashier_id=None,
        number="O-TEST",
        order_type=OrderType.DINE_IN,
        status=OrderStatus.OPEN,
        currency="BDT",
    )
    db_session.add(order)
    await db_session.flush()

    product = Product(
        tenant_id=tenant.id,
        sku="BURGER",
        barcode=None,
        name="Burger",
        description=None,
        category_id=None,
        price_cents=500,
        currency="BDT",
        is_active=True,
        track_inventory=False,
        tax_rate=0,  # type: ignore[arg-type]
        vertical_data={},
    )
    await ProductRepository(db_session).add(product)

    service = RestaurantService(db_session)
    ticket = await service.fire_kot(
        tenant_id=tenant.id,
        order_id=order.id,
        station=KdsStation.KITCHEN,
        items=[KotItemInput(product_id=product.id, name_snapshot="Burger", quantity=2)],
    )

    assert ticket.status == KotStatus.NEW
    assert ticket.number.startswith("K-")

    kitchen_queue = await service.list_station_tickets(
        tenant_id=tenant.id, station=KdsStation.KITCHEN
    )
    assert any(t.id == ticket.id for t in kitchen_queue)

    updated = await service.update_kot_status(
        tenant_id=tenant.id, ticket_id=ticket.id, status=KotStatus.READY
    )
    assert updated.status == KotStatus.READY
    assert updated.ready_at is not None

    # OrderRepository sanity — the order exists
    assert await OrderRepository(db_session).get_with_relations(
        tenant_id=tenant.id, order_id=order.id
    ) is not None
