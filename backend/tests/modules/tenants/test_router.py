"""Full HTTP round-trip for /tenant — current, update, permission guardrails."""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from src.core.security import issue_token
from src.main import create_app
from src.modules.identity.entity import User
from src.modules.identity.repository import UserRepository
from src.modules.tenants.repository import TenantRepository


async def _seed(db_session, *, roles: list[str] = ["owner"]):  # type: ignore[no-untyped-def]
    tenant = await TenantRepository(db_session).create(
        slug="http-tenant", name="Existing Name", country="BD", default_currency="BDT"
    )
    user = User(
        tenant_id=tenant.id,
        email="owner@example.com",
        first_name="Owner",
        last_name="One",
        password_hash=None,
        email_verified=True,
        roles=roles,
        terms_accepted_at=None,
    )
    await UserRepository(db_session).add(user)
    await db_session.commit()
    access = issue_token(subject=str(user.id), kind="access", tenant_id=str(tenant.id))
    return tenant, user, access


@pytest.mark.asyncio
async def test_get_current_tenant_returns_tenant_for_its_user(db_session):
    tenant, _, access = await _seed(db_session)
    app = create_app()
    headers = {"Authorization": f"Bearer {access}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/tenant", headers=headers)

    assert resp.status_code == 200
    body = resp.json()
    assert body["slug"] == tenant.slug
    assert body["name"] == "Existing Name"
    assert body["defaultCurrency"] == "BDT"


@pytest.mark.asyncio
async def test_get_current_tenant_requires_auth():
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/tenant")
    assert resp.status_code == 401
    envelope = resp.json()
    assert set(envelope.keys()) == {"error"}


@pytest.mark.asyncio
async def test_update_tenant_owner_can_change_name_currency_country(db_session):
    tenant, _, access = await _seed(db_session)
    app = create_app()
    headers = {"Authorization": f"Bearer {access}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.patch(
            "/tenant",
            json={"name": "Rebranded", "country": "us", "defaultCurrency": "usd"},
            headers=headers,
        )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["name"] == "Rebranded"
    assert body["country"] == "US"
    assert body["defaultCurrency"] == "USD"


@pytest.mark.asyncio
async def test_update_tenant_validates_currency_length(db_session):
    _, _, access = await _seed(db_session)
    app = create_app()
    headers = {"Authorization": f"Bearer {access}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.patch(
            "/tenant",
            json={"defaultCurrency": "TOOLONG"},
            headers=headers,
        )

    assert resp.status_code == 422
    envelope = resp.json()
    assert set(envelope.keys()) == {"error"}


@pytest.mark.asyncio
async def test_update_tenant_forbidden_for_non_admin_role(db_session):
    _, _, access = await _seed(db_session, roles=["cashier"])
    app = create_app()
    headers = {"Authorization": f"Bearer {access}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.patch(
            "/tenant",
            json={"name": "Nope"},
            headers=headers,
        )

    assert resp.status_code == 403
    envelope = resp.json()
    assert set(envelope.keys()) == {"error"}


@pytest.mark.asyncio
async def test_update_tenant_partial_leaves_unset_fields_intact(db_session):
    tenant, _, access = await _seed(db_session)
    app = create_app()
    headers = {"Authorization": f"Bearer {access}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.patch(
            "/tenant",
            json={"name": "Only Name"},
            headers=headers,
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Only Name"
    assert body["country"] == "BD"
    assert body["defaultCurrency"] == "BDT"
