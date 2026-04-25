"""Customer service — list/search, create, update, delete."""

from __future__ import annotations

import pytest

from src.core.errors import NotFoundError
from src.modules.customers.schemas import CustomerCreate, CustomerUpdate
from src.modules.customers.service import CustomerService
from src.modules.tenants.repository import TenantRepository


async def _tenant(db_session):  # type: ignore[no-untyped-def]
    return await TenantRepository(db_session).create(
        slug="c-tenant", name="Customers", country="BD", default_currency="BDT"
    )


@pytest.mark.asyncio
async def test_create_and_get_roundtrip(db_session):
    tenant = await _tenant(db_session)
    service = CustomerService(db_session)

    created = await service.create(
        tenant_id=tenant.id,
        actor_id=None,
        data=CustomerCreate(
            first_name="Ada",
            last_name="Lovelace",
            email="ada@example.com",
            phone="01700000000",
        ),
    )
    assert created.email == "ada@example.com"

    fetched = await service.get(tenant_id=tenant.id, customer_id=created.id)
    assert fetched.id == created.id


@pytest.mark.asyncio
async def test_list_with_search(db_session):
    tenant = await _tenant(db_session)
    service = CustomerService(db_session)
    for first in ("Ada", "Grace", "Alan"):
        await service.create(
            tenant_id=tenant.id,
            actor_id=None,
            data=CustomerCreate(first_name=first, email=f"{first.lower()}@ex.com"),
        )

    rows, _ = await service.list(
        tenant_id=tenant.id, search="grace", page=1, page_size=25
    )
    assert [c.first_name for c in rows] == ["Grace"]


@pytest.mark.asyncio
async def test_update_replaces_fields(db_session):
    tenant = await _tenant(db_session)
    service = CustomerService(db_session)
    c = await service.create(
        tenant_id=tenant.id,
        actor_id=None,
        data=CustomerCreate(first_name="Ada", email="ada@ex.com"),
    )
    updated = await service.update(
        tenant_id=tenant.id,
        customer_id=c.id,
        data=CustomerUpdate(phone="01999"),
    )
    assert updated.phone == "01999"


@pytest.mark.asyncio
async def test_delete_removes_customer(db_session):
    tenant = await _tenant(db_session)
    service = CustomerService(db_session)
    c = await service.create(
        tenant_id=tenant.id,
        actor_id=None,
        data=CustomerCreate(first_name="Ada", email="ada@ex.com"),
    )
    await service.delete(tenant_id=tenant.id, customer_id=c.id)
    with pytest.raises(NotFoundError):
        await service.get(tenant_id=tenant.id, customer_id=c.id)
