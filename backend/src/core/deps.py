"""Common FastAPI dependencies.

- ``get_db`` — yields an async session (commit/rollback)
- ``get_current_user`` — verifies the access JWT from Authorization header
- ``requires`` — permission dependency factory (RBAC)
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Cookie, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db import get_session
from src.core.errors import ForbiddenError, UnauthorizedError
from src.core.permissions import Permission, Role, permissions_for
from src.core.security import decode_token
from src.modules.identity.repository import UserRepository

DbSession = Annotated[AsyncSession, Depends(get_session)]

REFRESH_COOKIE_NAME = "bytloop_refresh"


def _extract_bearer(authorization: str | None) -> str:
    if not authorization:
        raise UnauthorizedError("Please sign in to continue.")
    prefix = "Bearer "
    if not authorization.startswith(prefix):
        raise UnauthorizedError("Invalid authorization header.")
    return authorization[len(prefix) :]


async def get_current_user_id(
    authorization: Annotated[str | None, Header()] = None,
) -> UUID:
    payload = decode_token(_extract_bearer(authorization), expected_kind="access")
    return UUID(payload.sub)


async def get_current_user(
    db: DbSession,
    user_id: Annotated[UUID, Depends(get_current_user_id)],
):
    users = UserRepository(db)
    user = await users.get_by_id(user_id)
    if user is None:
        raise UnauthorizedError("Account not found.")
    return user


def refresh_cookie(
    token: Annotated[str | None, Cookie(alias=REFRESH_COOKIE_NAME)] = None,
) -> str:
    if not token:
        raise UnauthorizedError("Missing refresh token.")
    return token


def requires(*required: Permission):
    """Dependency factory — enforces RBAC.

    Usage::
        @router.post("/foo", dependencies=[Depends(requires(Permission.ORDERS_CREATE))])
    """

    async def _check(user=Depends(get_current_user)) -> None:  # type: ignore[no-untyped-def]
        roles = [Role(r) for r in user.roles if r in Role.__members__.values()]
        granted = permissions_for(roles)
        for perm in required:
            if perm not in granted:
                raise ForbiddenError("You don't have permission to do that.")

    return _check
