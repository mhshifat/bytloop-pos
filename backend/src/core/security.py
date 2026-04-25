"""Password hashing (Argon2) + JWT issuance/verification."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Literal

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import JWTError, jwt

from src.core.config import settings
from src.core.errors import UnauthorizedError

TokenKind = Literal["access", "refresh", "activation", "password_reset"]


def _hasher() -> PasswordHasher:
    return PasswordHasher(
        time_cost=settings.auth.argon2_time_cost,
        memory_cost=settings.auth.argon2_memory_cost_kib,
    )


def hash_password(plain: str) -> str:
    return _hasher().hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return _hasher().verify(hashed, plain)
    except VerifyMismatchError:
        return False


@dataclass(frozen=True, slots=True)
class TokenPayload:
    sub: str
    kind: TokenKind
    tenant_id: str | None
    exp: int
    iat: int


def _ttl(kind: TokenKind) -> int:
    match kind:
        case "access":
            return settings.auth.access_token_ttl_seconds
        case "refresh":
            return settings.auth.refresh_token_ttl_seconds
        case "activation":
            return settings.auth.activation_token_ttl_seconds
        case "password_reset":
            return settings.auth.password_reset_token_ttl_seconds


def issue_token(
    *,
    subject: str,
    kind: TokenKind,
    tenant_id: str | None = None,
    extra: dict[str, Any] | None = None,
) -> str:
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": subject,
        "kind": kind,
        "iat": now,
        "exp": now + _ttl(kind),
    }
    if tenant_id:
        payload["tid"] = tenant_id
    if extra:
        payload.update(extra)
    return jwt.encode(
        payload,
        settings.auth.jwt_secret.get_secret_value(),
        algorithm=settings.auth.jwt_algorithm,
    )


def decode_token(token: str, *, expected_kind: TokenKind) -> TokenPayload:
    try:
        claims = jwt.decode(
            token,
            settings.auth.jwt_secret.get_secret_value(),
            algorithms=[settings.auth.jwt_algorithm],
        )
    except JWTError as exc:
        raise UnauthorizedError("Your session is invalid. Please sign in again.") from exc

    if claims.get("kind") != expected_kind:
        raise UnauthorizedError("Token kind mismatch.")

    sub = claims.get("sub")
    if not isinstance(sub, str):
        raise UnauthorizedError("Malformed token.")

    return TokenPayload(
        sub=sub,
        kind=expected_kind,
        tenant_id=claims.get("tid") if isinstance(claims.get("tid"), str) else None,
        exp=int(claims["exp"]),
        iat=int(claims["iat"]),
    )
