"""OAuth provider configuration (Authlib).

Google and GitHub redirects share the same two-leg flow:
  1. GET /auth/{provider}/start → redirect to provider's consent URL
  2. GET /auth/{provider}/callback?code=… → exchange code, fetch profile,
     call IdentityService.complete_oauth, set refresh cookie, redirect to FE.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App

from src.core.config import settings

Provider = Literal["google", "github"]


@lru_cache(maxsize=1)
def _oauth() -> OAuth:
    oauth = OAuth()
    if settings.auth.google_client_id:
        oauth.register(
            name="google",
            client_id=settings.auth.google_client_id,
            client_secret=settings.auth.google_client_secret.get_secret_value(),
            server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
            client_kwargs={"scope": "openid email profile"},
        )
    if settings.auth.github_client_id:
        oauth.register(
            name="github",
            client_id=settings.auth.github_client_id,
            client_secret=settings.auth.github_client_secret.get_secret_value(),
            access_token_url="https://github.com/login/oauth/access_token",
            authorize_url="https://github.com/login/oauth/authorize",
            api_base_url="https://api.github.com/",
            client_kwargs={"scope": "read:user user:email"},
        )
    return oauth


def client_for(provider: Provider) -> StarletteOAuth2App:
    client = _oauth().create_client(provider)
    if client is None:
        from src.core.errors import AppError

        raise AppError(
            f"{provider.title()} sign-in isn't available right now.",
            code="oauth_not_configured",
        )
    return client


def frontend_redirect_url(path: str = "/dashboard") -> str:
    base = settings.auth.oauth_redirect_base_url.rstrip("/")
    return f"{base}{path}"
