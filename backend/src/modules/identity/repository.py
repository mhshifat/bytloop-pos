from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.identity.entity import OAuthAccount, OAuthProvider, User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str, *, tenant_id: UUID) -> User | None:
        stmt = select(User).where(
            User.email == email.lower(),
            User.tenant_id == tenant_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def get_any_by_email(self, email: str) -> User | None:
        """For signup uniqueness / login lookup before tenant resolution."""
        stmt = select(User).where(User.email == email.lower())
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def add(self, user: User) -> User:
        self._session.add(user)
        await self._session.flush()
        return user

    async def set_verified(self, user: User) -> None:
        user.email_verified = True
        await self._session.flush()

    async def set_password(self, user: User, *, password_hash: str) -> None:
        user.password_hash = password_hash
        await self._session.flush()

    async def list_for_tenant(self, *, tenant_id: UUID) -> list[User]:
        stmt = (
            select(User)
            .where(User.tenant_id == tenant_id)
            .order_by(User.first_name, User.last_name)
        )
        return list((await self._session.execute(stmt)).scalars().all())


class OAuthAccountRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def find(self, *, provider: OAuthProvider, provider_account_id: str) -> OAuthAccount | None:
        stmt = select(OAuthAccount).where(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_account_id == provider_account_id,
        )
        return (await self._session.execute(stmt)).scalar_one_or_none()

    async def link(
        self, *, user_id: UUID, provider: OAuthProvider, provider_account_id: str
    ) -> OAuthAccount:
        link = OAuthAccount(
            user_id=user_id,
            provider=provider,
            provider_account_id=provider_account_id,
        )
        self._session.add(link)
        await self._session.flush()
        return link
