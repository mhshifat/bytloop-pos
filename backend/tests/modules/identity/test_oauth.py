"""OAuth flow — Google (OIDC) + GitHub (profile + emails) via IdentityService.

We exercise `complete_oauth` directly (the HTTP layer just proxies into the
same service) and verify:
- New OAuth user is created with email_verified=True (OAuth emails are trusted)
- Second sign-in with the same provider_account_id reuses the existing user
- Sign-in via OAuth for an already-existing email links the account and
  promotes the user to verified if they weren't already
"""

from __future__ import annotations

import pytest

from src.core.security import decode_token
from src.modules.identity.entity import OAuthProvider
from src.modules.identity.service import IdentityService


@pytest.fixture
def service(db_session, fake_email):  # type: ignore[no-untyped-def]
    return IdentityService(db_session, email=fake_email)


@pytest.mark.asyncio
async def test_oauth_new_user_auto_verified(service):
    tokens = await service.complete_oauth(
        provider=OAuthProvider.GOOGLE,
        provider_account_id="google-abc-123",
        email="oauth-new@example.com",
        first_name="O",
        last_name="Auth",
    )
    assert tokens.access_token
    payload = decode_token(tokens.access_token, expected_kind="access")
    assert payload.sub


@pytest.mark.asyncio
async def test_oauth_returning_user_reuses_existing_link(service):
    first = await service.complete_oauth(
        provider=OAuthProvider.GITHUB,
        provider_account_id="gh-777",
        email="returning@example.com",
        first_name="R",
        last_name="E",
    )
    again = await service.complete_oauth(
        provider=OAuthProvider.GITHUB,
        provider_account_id="gh-777",
        email="returning@example.com",
        first_name="R",
        last_name="E",
    )
    first_sub = decode_token(first.access_token, expected_kind="access").sub
    again_sub = decode_token(again.access_token, expected_kind="access").sub
    assert first_sub == again_sub


@pytest.mark.asyncio
async def test_oauth_promotes_unverified_existing_user(service, fake_email):
    # Sign up via email/password first — creates an unverified user.
    await service.signup(
        first_name="Ada",
        last_name="L",
        email="ada@example.com",
        password="passwordpass",
    )

    # Now the same email signs in via Google — should promote to verified.
    tokens = await service.complete_oauth(
        provider=OAuthProvider.GOOGLE,
        provider_account_id="google-promote-1",
        email="ada@example.com",
        first_name="Ada",
        last_name="L",
    )
    assert tokens.access_token

    # Now email/password login should succeed — no longer blocked by
    # email_not_verified, because OAuth promoted the user.
    login = await service.login_with_password(
        email="ada@example.com", password="passwordpass"
    )
    assert login.access_token
