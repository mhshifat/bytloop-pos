"""Identity service tests — TDD for the critical auth flows."""

from __future__ import annotations

import pytest

from src.core.errors import ConflictError, ForbiddenError, RateLimitError, UnauthorizedError
from src.core.security import issue_token
from src.modules.identity.entity import OAuthProvider
from src.modules.identity.service import IdentityService


@pytest.fixture
def service(db_session, fake_email):  # type: ignore[no-untyped-def]
    return IdentityService(db_session, email=fake_email)


@pytest.mark.asyncio
async def test_signup_creates_unverified_user_and_sends_activation(service, fake_email):
    user = await service.signup(
        first_name="Ada", last_name="Lovelace", email="ada@example.com", password="hunter2pass"
    )
    assert user.email == "ada@example.com"
    assert user.email_verified is False
    assert user.password_hash is not None
    assert len(fake_email.sent) == 1


@pytest.mark.asyncio
async def test_signup_rejects_duplicate_email(service):
    await service.signup(
        first_name="Ada", last_name="L", email="dupe@example.com", password="passwordpass"
    )
    with pytest.raises(ConflictError):
        await service.signup(
            first_name="Ada", last_name="L", email="dupe@example.com", password="passwordpass"
        )


@pytest.mark.asyncio
async def test_password_login_forbidden_when_unverified(service):
    await service.signup(
        first_name="A", last_name="B", email="u@example.com", password="passwordpass"
    )
    with pytest.raises(ForbiddenError):
        await service.login_with_password(email="u@example.com", password="passwordpass")


@pytest.mark.asyncio
async def test_activation_flips_verified_flag_and_login_succeeds(service):
    user = await service.signup(
        first_name="A", last_name="B", email="v@example.com", password="passwordpass"
    )
    token = issue_token(subject=str(user.id), kind="activation", tenant_id=str(user.tenant_id))
    await service.activate(token=token)

    tokens = await service.login_with_password(email="v@example.com", password="passwordpass")
    assert tokens.access_token
    assert tokens.refresh_token
    assert tokens.access_ttl_seconds == 86400


@pytest.mark.asyncio
async def test_wrong_password_rejected_with_generic_message(service):
    user = await service.signup(
        first_name="A", last_name="B", email="bad@example.com", password="passwordpass"
    )
    token = issue_token(subject=str(user.id), kind="activation", tenant_id=str(user.tenant_id))
    await service.activate(token=token)

    with pytest.raises(UnauthorizedError):
        await service.login_with_password(email="bad@example.com", password="wrongwrong")


@pytest.mark.asyncio
async def test_refresh_issues_new_access_token(service):
    user = await service.signup(
        first_name="A", last_name="B", email="r@example.com", password="passwordpass"
    )
    token = issue_token(subject=str(user.id), kind="activation", tenant_id=str(user.tenant_id))
    await service.activate(token=token)

    first = await service.login_with_password(email="r@example.com", password="passwordpass")
    refreshed = await service.refresh(refresh_token=first.refresh_token)
    assert refreshed.access_token


@pytest.mark.asyncio
async def test_oauth_auto_verifies_new_user(service, fake_email):
    tokens = await service.complete_oauth(
        provider=OAuthProvider.GOOGLE,
        provider_account_id="google-12345",
        email="oauth@example.com",
        first_name="O",
        last_name="A",
    )
    assert tokens.access_token
    # No activation email sent — OAuth is auto-verified.
    assert fake_email.sent == []


@pytest.mark.asyncio
async def test_oauth_reuses_existing_link(service):
    await service.complete_oauth(
        provider=OAuthProvider.GITHUB,
        provider_account_id="gh-999",
        email="gh@example.com",
        first_name="G",
        last_name="H",
    )
    again = await service.complete_oauth(
        provider=OAuthProvider.GITHUB,
        provider_account_id="gh-999",
        email="gh@example.com",
        first_name="G",
        last_name="H",
    )
    assert again.access_token


@pytest.mark.asyncio
async def test_resend_activation_rate_limited_after_first_send(monkeypatch, service):
    """Second resend within the cooldown window must raise RateLimitError."""
    state = {"ttl": 0}

    async def fake_ttl(_key: str) -> int | None:
        return state["ttl"] or None

    async def fake_set(_key: str, _value: str, *, ttl_seconds: int) -> bool:
        state["ttl"] = ttl_seconds
        return True

    from src.core import cache

    monkeypatch.setattr(cache, "ttl", fake_ttl)
    monkeypatch.setattr(cache, "set_str", fake_set)

    await service.signup(
        first_name="A", last_name="B", email="resend@example.com", password="passwordpass"
    )

    await service.resend_activation(email="resend@example.com")
    with pytest.raises(RateLimitError):
        await service.resend_activation(email="resend@example.com")
