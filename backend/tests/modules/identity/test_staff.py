"""Staff management — invite, role update, remove, guardrails."""

from __future__ import annotations

import pytest

from src.core.errors import ConflictError, ForbiddenError, NotFoundError, ValidationError
from src.modules.identity.repository import UserRepository
from src.modules.identity.service import IdentityService
from src.modules.tenants.repository import TenantRepository


@pytest.fixture
def service(db_session, fake_email):  # type: ignore[no-untyped-def]
    return IdentityService(db_session, email=fake_email)


@pytest.fixture
async def owner(service, db_session):  # type: ignore[no-untyped-def]
    """An existing verified owner under their own tenant."""
    user = await service.signup(
        first_name="Ada",
        last_name="Owner",
        email="owner@example.com",
        password="ownerpass123",
    )
    # Mark verified so invite flows can proceed from a real tenant context.
    await UserRepository(db_session).set_verified(user)
    return user


@pytest.mark.asyncio
async def test_invite_creates_unverified_staff_in_same_tenant(service, owner, fake_email):
    invited = await service.invite_staff(
        tenant_id=owner.tenant_id,
        actor_id=owner.id,
        email="cashier@example.com",
        first_name="Cash",
        last_name="Ier",
        roles=["cashier"],
    )
    assert invited.tenant_id == owner.tenant_id
    assert invited.email_verified is False
    assert invited.password_hash is None
    assert list(invited.roles) == ["cashier"]
    # Owner's signup email + invite email.
    assert len(fake_email.sent) == 2


@pytest.mark.asyncio
async def test_invite_rejects_duplicate_email(service, owner):
    await service.invite_staff(
        tenant_id=owner.tenant_id,
        actor_id=owner.id,
        email="dup@example.com",
        first_name="D",
        last_name="U",
        roles=["cashier"],
    )
    with pytest.raises(ConflictError):
        await service.invite_staff(
            tenant_id=owner.tenant_id,
            actor_id=owner.id,
            email="dup@example.com",
            first_name="D",
            last_name="U",
            roles=["cashier"],
        )


@pytest.mark.asyncio
async def test_invite_rejects_empty_roles(service, owner):
    with pytest.raises(ValidationError):
        await service.invite_staff(
            tenant_id=owner.tenant_id,
            actor_id=owner.id,
            email="empty@example.com",
            first_name="E",
            last_name="R",
            roles=[],
        )


@pytest.mark.asyncio
async def test_update_roles_replaces_the_role_list(service, owner):
    invited = await service.invite_staff(
        tenant_id=owner.tenant_id,
        actor_id=owner.id,
        email="roles@example.com",
        first_name="R",
        last_name="L",
        roles=["cashier"],
    )
    updated = await service.update_staff_roles(
        tenant_id=owner.tenant_id,
        actor_id=owner.id,
        user_id=invited.id,
        roles=["manager", "cashier"],
    )
    assert set(updated.roles) == {"manager", "cashier"}


@pytest.mark.asyncio
async def test_update_roles_prevents_owner_self_downgrade(service, owner):
    with pytest.raises(ForbiddenError):
        await service.update_staff_roles(
            tenant_id=owner.tenant_id,
            actor_id=owner.id,
            user_id=owner.id,
            roles=["cashier"],
        )


@pytest.mark.asyncio
async def test_update_roles_rejects_cross_tenant_target(service, owner, db_session):
    other_tenant = await TenantRepository(db_session).create(
        slug="other-co", name="Other Co", country="BD", default_currency="BDT"
    )
    # Put a user in another tenant
    stranger = await service.invite_staff(
        tenant_id=other_tenant.id,
        actor_id=owner.id,  # audit only — doesn't affect tenant isolation check
        email="stranger@example.com",
        first_name="S",
        last_name="T",
        roles=["cashier"],
    )
    with pytest.raises(NotFoundError):
        await service.update_staff_roles(
            tenant_id=owner.tenant_id,
            actor_id=owner.id,
            user_id=stranger.id,
            roles=["manager"],
        )


@pytest.mark.asyncio
async def test_remove_blocks_self_removal(service, owner):
    with pytest.raises(ForbiddenError):
        await service.remove_staff(
            tenant_id=owner.tenant_id, actor_id=owner.id, user_id=owner.id
        )


@pytest.mark.asyncio
async def test_remove_deletes_the_user(service, owner, db_session):
    invited = await service.invite_staff(
        tenant_id=owner.tenant_id,
        actor_id=owner.id,
        email="rm@example.com",
        first_name="R",
        last_name="M",
        roles=["cashier"],
    )
    await service.remove_staff(
        tenant_id=owner.tenant_id, actor_id=owner.id, user_id=invited.id
    )
    assert await UserRepository(db_session).get_by_id(invited.id) is None


@pytest.mark.asyncio
async def test_remove_rejects_cross_tenant_target(service, owner, db_session):
    other_tenant = await TenantRepository(db_session).create(
        slug="other-rm", name="Other Rm", country="BD", default_currency="BDT"
    )
    stranger = await service.invite_staff(
        tenant_id=other_tenant.id,
        actor_id=owner.id,
        email="stranger-rm@example.com",
        first_name="S",
        last_name="R",
        roles=["cashier"],
    )
    with pytest.raises(NotFoundError):
        await service.remove_staff(
            tenant_id=owner.tenant_id, actor_id=owner.id, user_id=stranger.id
        )
