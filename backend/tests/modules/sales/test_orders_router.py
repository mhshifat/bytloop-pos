"""Full HTTP round-trip for /orders — checkout, list, detail, void, refund."""

from __future__ import annotations

from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.security import issue_token
from src.main import create_app
from src.modules.catalog.entity import Product
from src.modules.catalog.repository import ProductRepository
from src.modules.identity.entity import User
from src.modules.identity.repository import UserRepository
from src.modules.tenants.repository import TenantRepository


@pytest.fixture
async def seeded(db_session):  # type: ignore[no-untyped-def]
    tenant = await TenantRepository(db_session).create(
        slug="http-sales", name="HTTP Sales", country="BD", default_currency="BDT"
    )
    user = User(
        tenant_id=tenant.id,
        email="cashier@example.com",
        first_name="Cashier",
        last_name="One",
        password_hash=None,
        email_verified=True,
        roles=["owner"],
        terms_accepted_at=None,
    )
    await UserRepository(db_session).add(user)

    product = Product(
        tenant_id=tenant.id,
        sku="TEST-1",
        barcode=None,
        name="Test item",
        description=None,
        category_id=None,
        price_cents=1500,
        currency="BDT",
        is_active=True,
        track_inventory=False,
        tax_rate=Decimal("0"),
        vertical_data={},
    )
    await ProductRepository(db_session).add(product)
    await db_session.commit()

    access = issue_token(
        subject=str(user.id), kind="access", tenant_id=str(tenant.id)
    )
    return {"tenant": tenant, "user": user, "product": product, "access": access}


@pytest.mark.asyncio
async def test_checkout_list_detail_and_void_roundtrip(seeded):
    app = create_app()
    headers = {"Authorization": f"Bearer {seeded['access']}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Checkout
        resp = await client.post(
            "/orders/checkout",
            json={
                "items": [{"productId": str(seeded["product"].id), "quantity": 2}],
                "paymentMethod": "cash",
                "amountTenderedCents": 3000,
            },
            headers=headers,
        )
        assert resp.status_code == 201, resp.text
        created = resp.json()
        order_id = created["id"]
        assert created["totalCents"] == 3000
        assert created["status"] == "completed"

        # List shows it
        resp = await client.get("/orders", headers=headers)
        assert resp.status_code == 200
        assert any(o["id"] == order_id for o in resp.json()["items"])

        # Detail round-trip
        resp = await client.get(f"/orders/{order_id}", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["number"] == created["number"]

        # Void it
        resp = await client.post(f"/orders/{order_id}/void", headers=headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "voided"

        # Voiding twice is rejected as validation_failed
        resp = await client.post(f"/orders/{order_id}/void", headers=headers)
        assert resp.status_code == 422
        envelope = resp.json()
        assert set(envelope.keys()) == {"error"}
        assert envelope["error"]["code"] == "validation_failed"
