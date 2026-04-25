"""Identity service — signup / activation / login / OAuth / reset flows.

Business logic owner. Routers delegate here; this is where transactions live.
See docs/PLAN.md §11.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from src.core import cache
from src.core.config import settings
from src.core.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    RateLimitError,
    UnauthorizedError,
    ValidationError,
)
from src.core.security import (
    decode_token,
    hash_password,
    issue_token,
    verify_password,
)
from src.integrations.email.base import EmailAdapter
from src.integrations.email.templates import activation_email, password_reset_email
from src.modules.audit.api import AuditService
from src.modules.identity.entity import OAuthAccount, OAuthProvider, User
from src.modules.identity.repository import OAuthAccountRepository, UserRepository
from src.modules.tenants.repository import TenantRepository

logger = structlog.get_logger(__name__)


@dataclass(frozen=True, slots=True)
class LoginTokens:
    access_token: str
    refresh_token: str
    access_ttl_seconds: int
    refresh_ttl_seconds: int


def _resend_key(email: str) -> str:
    return f"pos:auth:resend:{email.lower()}"


def _login_failure_key(email: str) -> str:
    return f"pos:auth:login_fail:{email.lower()}"


MAX_LOGIN_ATTEMPTS = 10
LOGIN_LOCKOUT_SECONDS = 300  # 5 min


def _activation_url(token: str) -> str:
    return f"{settings.auth.oauth_redirect_base_url.rstrip('/')}/activate?token={token}"


def _reset_url(token: str) -> str:
    return f"{settings.auth.oauth_redirect_base_url.rstrip('/')}/reset-password?token={token}"


class IdentityService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        email: EmailAdapter,
        users: UserRepository | None = None,
        oauth_accounts: OAuthAccountRepository | None = None,
        tenants: TenantRepository | None = None,
    ) -> None:
        self._session = session
        self._email = email
        self._users = users or UserRepository(session)
        self._oauth = oauth_accounts or OAuthAccountRepository(session)
        self._tenants = tenants or TenantRepository(session)

    # ──────────────────────────────────────────────
    # Signup
    # ──────────────────────────────────────────────

    async def signup(
        self,
        *,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
    ) -> User:
        existing = await self._users.get_any_by_email(email)
        if existing is not None:
            raise ConflictError("An account with that email already exists.")

        # Bootstrap: self-service signup creates a per-user tenant. Real
        # multi-tenant onboarding flows (invitations) replace this later.
        tenant = await self._tenants.create(
            slug=email.split("@", 1)[0].lower()[:32] + "-" + str(UUID(int=0))[:8],
            name=f"{first_name}'s workspace",
            country="BD",
            default_currency=settings.currency.default,
        )

        user = User(
            tenant_id=tenant.id,
            email=email.lower(),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            password_hash=hash_password(password),
            email_verified=False,
            roles=["owner"],
            terms_accepted_at=datetime.now(tz=UTC),
        )
        await self._users.add(user)
        await AuditService(self._session).record(
            tenant_id=tenant.id,
            actor_id=user.id,
            action="user.signup",
            resource_type="user",
            resource_id=str(user.id),
            after={"email": user.email, "roles": list(user.roles)},
        )
        await self._send_activation(user)
        return user

    async def _send_activation(self, user: User) -> None:
        token = issue_token(
            subject=str(user.id), kind="activation", tenant_id=str(user.tenant_id)
        )
        message = activation_email(
            to=user.email,
            first_name=user.first_name,
            activation_url=_activation_url(token),
        )
        # Inline send keeps the contract simple (and tests can inject a fake
        # adapter). In production, swap the injected adapter for one that
        # enqueues via `src.tasks.email_tasks.enqueue_email` to push SMTP
        # latency off the request path.
        await self._email.send(message)
        logger.info("activation_sent", user_id=str(user.id), email=user.email)

    # ──────────────────────────────────────────────
    # Activation
    # ──────────────────────────────────────────────

    async def activate(self, *, token: str) -> None:
        payload = decode_token(token, expected_kind="activation")
        user = await self._users.get_by_id(UUID(payload.sub))
        if user is None:
            raise NotFoundError("We couldn't find that account.")
        if user.email_verified:
            return  # idempotent
        await self._users.set_verified(user)
        await AuditService(self._session).record(
            tenant_id=user.tenant_id,
            actor_id=user.id,
            action="user.email_verified",
            resource_type="user",
            resource_id=str(user.id),
        )

    async def resend_activation(self, *, email: str) -> int:
        """Return remaining cooldown seconds (0 when freshly sent)."""
        user = await self._users.get_any_by_email(email)
        if user is None or user.email_verified:
            # Don't disclose whether the email exists; pretend success.
            return 0

        key = _resend_key(user.email)
        remaining = await cache.ttl(key)
        if remaining is not None and remaining > 0:
            raise RateLimitError(
                f"Please wait {remaining}s before requesting another email.",
                details={"cooldownRemainingSeconds": remaining},
            )

        await self._send_activation(user)
        await cache.set_str(key, "1", ttl_seconds=settings.auth.resend_cooldown_seconds)
        return 0

    # ──────────────────────────────────────────────
    # Login
    # ──────────────────────────────────────────────

    async def login_with_password(self, *, email: str, password: str) -> LoginTokens:
        fail_key = _login_failure_key(email)
        # Soft rate limit — if Redis is down the cache wrapper returns None and we
        # fail open (logging only). Prevents credential-stuffing bursts.
        current_fails = await cache.get_str(fail_key)
        if current_fails and int(current_fails) >= MAX_LOGIN_ATTEMPTS:
            raise RateLimitError(
                "Too many failed attempts. Please wait a few minutes.",
                details={"cooldownRemainingSeconds": LOGIN_LOCKOUT_SECONDS},
            )

        user = await self._users.get_any_by_email(email)
        if user is None or user.password_hash is None:
            await self._record_login_failure(fail_key)
            raise UnauthorizedError("Invalid email or password.")
        if not verify_password(password, user.password_hash):
            await self._record_login_failure(fail_key)
            raise UnauthorizedError("Invalid email or password.")
        if not user.email_verified:
            raise ForbiddenError(
                "Please verify your email before signing in.",
                code="email_not_verified",
            )
        # Successful login — clear the fail counter.
        await cache.delete(fail_key)
        return self._issue_tokens(user)

    async def _record_login_failure(self, key: str) -> None:
        current = await cache.get_str(key)
        count = (int(current) if current else 0) + 1
        await cache.set_str(key, str(count), ttl_seconds=LOGIN_LOCKOUT_SECONDS)

    def _issue_tokens(self, user: User) -> LoginTokens:
        access = issue_token(
            subject=str(user.id), kind="access", tenant_id=str(user.tenant_id)
        )
        refresh = issue_token(
            subject=str(user.id), kind="refresh", tenant_id=str(user.tenant_id)
        )
        return LoginTokens(
            access_token=access,
            refresh_token=refresh,
            access_ttl_seconds=settings.auth.access_token_ttl_seconds,
            refresh_ttl_seconds=settings.auth.refresh_token_ttl_seconds,
        )

    async def refresh(self, *, refresh_token: str) -> LoginTokens:
        payload = decode_token(refresh_token, expected_kind="refresh")
        user = await self._users.get_by_id(UUID(payload.sub))
        if user is None:
            raise UnauthorizedError("Your session has expired.")
        return self._issue_tokens(user)

    # ──────────────────────────────────────────────
    # OAuth (Google / GitHub) — auto-verifies email
    # ──────────────────────────────────────────────

    async def complete_oauth(
        self,
        *,
        provider: OAuthProvider,
        provider_account_id: str,
        email: str,
        first_name: str,
        last_name: str,
    ) -> LoginTokens:
        link: OAuthAccount | None = await self._oauth.find(
            provider=provider, provider_account_id=provider_account_id
        )
        if link is not None:
            user = await self._users.get_by_id(link.user_id)
            if user is None:
                raise NotFoundError("Linked account no longer exists.")
            return self._issue_tokens(user)

        user = await self._users.get_any_by_email(email)
        if user is None:
            tenant = await self._tenants.create(
                slug=email.split("@", 1)[0].lower()[:32] + "-" + str(UUID(int=0))[:8],
                name=f"{first_name}'s workspace",
                country="BD",
                default_currency=settings.currency.default,
            )
            user = User(
                tenant_id=tenant.id,
                email=email.lower(),
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                password_hash=None,
                email_verified=True,  # OAuth emails are trusted
                roles=["owner"],
                terms_accepted_at=datetime.now(tz=UTC),
            )
            await self._users.add(user)
        elif not user.email_verified:
            await self._users.set_verified(user)

        await self._oauth.link(
            user_id=user.id,
            provider=provider,
            provider_account_id=provider_account_id,
        )
        return self._issue_tokens(user)

    # ──────────────────────────────────────────────
    # Password reset
    # ──────────────────────────────────────────────

    async def send_password_reset(self, *, email: str) -> None:
        user = await self._users.get_any_by_email(email)
        if user is None:
            return  # silent to prevent enumeration
        token = issue_token(
            subject=str(user.id), kind="password_reset", tenant_id=str(user.tenant_id)
        )
        message = password_reset_email(
            to=user.email, first_name=user.first_name, reset_url=_reset_url(token)
        )
        await self._email.send(message)

    async def reset_password(self, *, token: str, new_password: str) -> None:
        payload = decode_token(token, expected_kind="password_reset")
        user = await self._users.get_by_id(UUID(payload.sub))
        if user is None:
            raise NotFoundError("Account not found.")
        await self._users.set_password(user, password_hash=hash_password(new_password))

    # ──────────────────────────────────────────────
    # Staff management (owner/manager only — guarded at the router layer)
    # ──────────────────────────────────────────────

    async def invite_staff(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        email: str,
        first_name: str,
        last_name: str,
        roles: list[str],
    ) -> User:
        existing = await self._users.get_any_by_email(email)
        if existing is not None:
            raise ConflictError("An account with that email already exists.")
        if not roles:
            raise ValidationError("At least one role is required.")

        user = User(
            tenant_id=tenant_id,
            email=email.lower(),
            first_name=first_name.strip(),
            last_name=last_name.strip(),
            password_hash=None,
            email_verified=False,
            roles=list(roles),
            terms_accepted_at=None,
        )
        await self._users.add(user)
        await AuditService(self._session).record(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="staff.invited",
            resource_type="user",
            resource_id=str(user.id),
            after={"email": user.email, "roles": list(user.roles)},
        )
        # The invited user completes activation via the same email flow as a
        # self-service signup — they click the link, set a password, and log in.
        await self._send_activation(user)
        return user

    async def update_staff_roles(
        self,
        *,
        tenant_id: UUID,
        actor_id: UUID,
        user_id: UUID,
        roles: list[str],
    ) -> User:
        if not roles:
            raise ValidationError("At least one role is required.")
        user = await self._users.get_by_id(user_id)
        if user is None or user.tenant_id != tenant_id:
            raise NotFoundError("Staff member not found.")
        if user.id == actor_id and "owner" not in roles and "owner" in user.roles:
            # Prevent accidental self-lockout: if you're the acting owner,
            # you can't strip your own owner role.
            raise ForbiddenError("You can't remove your own owner role.")
        previous = list(user.roles)
        user.roles = list(roles)
        await self._session.flush()
        await AuditService(self._session).record(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="staff.roles_updated",
            resource_type="user",
            resource_id=str(user.id),
            before={"roles": previous},
            after={"roles": list(user.roles)},
        )
        return user

    async def remove_staff(
        self, *, tenant_id: UUID, actor_id: UUID, user_id: UUID
    ) -> None:
        if actor_id == user_id:
            raise ForbiddenError("You can't remove your own account.")
        user = await self._users.get_by_id(user_id)
        if user is None or user.tenant_id != tenant_id:
            raise NotFoundError("Staff member not found.")
        # Keep the audit trail intact — soft-delete semantics via tenant_id
        # would be nicer long term; for now the simple hard-delete is fine
        # because the audit row survives (no FK back to users).
        await self._session.delete(user)
        await self._session.flush()
        await AuditService(self._session).record(
            tenant_id=tenant_id,
            actor_id=actor_id,
            action="staff.removed",
            resource_type="user",
            resource_id=str(user_id),
            before={"email": user.email, "roles": list(user.roles)},
        )

    async def change_password(
        self, *, user_id: UUID, current_password: str, new_password: str
    ) -> None:
        user = await self._users.get_by_id(user_id)
        if user is None or user.password_hash is None:
            raise UnauthorizedError("Your account has no password set.")
        if not verify_password(current_password, user.password_hash):
            raise UnauthorizedError("Current password is incorrect.")
        if len(new_password) < settings.auth.password_min_length:
            raise ValidationError(
                f"Password must be at least {settings.auth.password_min_length} characters."
            )
        await self._users.set_password(user, password_hash=hash_password(new_password))
        await AuditService(self._session).record(
            tenant_id=user.tenant_id,
            actor_id=user.id,
            action="user.password_changed",
            resource_type="user",
            resource_id=str(user.id),
        )
