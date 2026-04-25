"""OAuth HTTP endpoints — Google + GitHub."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from src.core.config import settings
from src.core.deps import DbSession, REFRESH_COOKIE_NAME
from src.integrations.email.factory import get_email_adapter
from src.modules.identity.entity import OAuthProvider
from src.modules.identity.oauth import Provider, client_for, frontend_redirect_url
from src.modules.identity.service import IdentityService, LoginTokens

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/{provider}/start")
async def oauth_start(provider: Provider, request: Request) -> RedirectResponse:
    client = client_for(provider)
    redirect_uri = str(request.url_for("oauth_callback", provider=provider))
    return await client.authorize_redirect(request, redirect_uri)  # type: ignore[no-any-return]


@router.get("/{provider}/callback", name="oauth_callback")
async def oauth_callback(
    provider: Provider, request: Request, db: DbSession
) -> RedirectResponse:
    client = client_for(provider)
    token = await client.authorize_access_token(request)

    email, first_name, last_name, provider_account_id = await _fetch_profile(
        provider, client, token
    )

    service = IdentityService(db, email=get_email_adapter())
    tokens = await service.complete_oauth(
        provider=OAuthProvider(provider),
        provider_account_id=provider_account_id,
        email=email,
        first_name=first_name,
        last_name=last_name,
    )

    response = RedirectResponse(frontend_redirect_url("/dashboard"))
    _set_refresh_cookie(response, tokens)
    return response


async def _fetch_profile(
    provider: Provider, client, token  # type: ignore[no-untyped-def]
) -> tuple[str, str, str, str]:
    if provider == "google":
        # OIDC — parse id_token claims that Authlib already verified.
        claims = token.get("userinfo") or await client.parse_id_token(token, None)  # type: ignore[attr-defined]
        email = str(claims["email"])
        full_name = str(claims.get("name", "")).strip()
        first, _, last = full_name.partition(" ")
        return (
            email,
            first or str(claims.get("given_name", email.split("@", 1)[0])),
            last or str(claims.get("family_name", "")),
            str(claims["sub"]),
        )

    # GitHub — call /user and /user/emails to get a verified primary email.
    user_resp = await client.get("user", token=token)
    user = user_resp.json()
    emails_resp = await client.get("user/emails", token=token)
    emails = emails_resp.json()
    primary = next(
        (e["email"] for e in emails if e.get("primary") and e.get("verified")),
        user.get("email") or "",
    )
    full_name = str(user.get("name") or "").strip()
    first, _, last = full_name.partition(" ")
    return (
        str(primary),
        first or str(user.get("login", "user")),
        last,
        str(user["id"]),
    )


def _set_refresh_cookie(response: RedirectResponse, tokens: LoginTokens) -> None:
    response.set_cookie(
        REFRESH_COOKIE_NAME,
        tokens.refresh_token,
        max_age=tokens.refresh_ttl_seconds,
        httponly=True,
        secure=settings.app.env == "production",
        samesite="lax",
        path="/",
    )
