"""Shared pytest fixtures.

Uses the LOCAL Postgres test database (``bytloop_pos_test``) — no Docker, no
containers. Schema is applied once per session via Alembic. Each test runs in
an outer transaction that is rolled back at teardown for perfect isolation.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from alembic import command
from alembic.config import Config
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

os.environ.setdefault("APP_SECRET_KEY", "test-secret")
os.environ.setdefault("AUTH_JWT_SECRET", "test-jwt-secret-0000000000000000000000000000")

# Point the app at the test DB *before* importing it.
TEST_DB_URL = os.environ.setdefault(
    "DATABASE_URL",
    os.environ.get("TEST_DATABASE_URL")
    or "postgresql+asyncpg://postgres:postgres@localhost:5432/bytloop_pos_test",
)


@pytest.fixture(scope="session")
def event_loop():  # type: ignore[no-untyped-def]
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def _apply_migrations() -> None:
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_DB_URL.replace("+asyncpg", ""))
    command.upgrade(cfg, "head")


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Transactional session — every test gets a clean slate via rollback."""
    engine = create_async_engine(TEST_DB_URL, poolclass=None)
    connection = await engine.connect()
    transaction = await connection.begin()

    factory = async_sessionmaker(bind=connection, expire_on_commit=False, class_=AsyncSession)
    session = factory()
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


class _FakeEmailAdapter:
    """Captures sent messages instead of sending."""

    def __init__(self) -> None:
        self.sent: list[object] = []

    async def send(self, message) -> None:  # type: ignore[no-untyped-def]
        self.sent.append(message)


@pytest.fixture
def fake_email() -> _FakeEmailAdapter:
    return _FakeEmailAdapter()
