"""Async SQLAlchemy engine + session factory.

Pool sized per docs/PLAN.md §15b. Fast pool timeout so a saturated Neon free
tier surfaces as a ``RateLimitError`` instead of a hung request.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from src.core.config import settings


def _async_database_url(url: str) -> str:
    """Use asyncpg — bare ``postgresql://`` would make SQLAlchemy try psycopg2 (not a dep)."""
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    return url


class Base(MappedAsDataclass, DeclarativeBase):
    """Project-wide declarative base. snake_case tables + columns."""


def _build_engine() -> AsyncEngine:
    return create_async_engine(
        _async_database_url(settings.database.url),
        pool_size=settings.database.pool_size,
        max_overflow=settings.database.max_overflow,
        pool_recycle=settings.database.pool_recycle_seconds,
        pool_timeout=settings.database.pool_timeout_seconds,
        pool_pre_ping=settings.database.pool_pre_ping,
        echo=False,
        future=True,
    )


engine: AsyncEngine = _build_engine()
async_session_factory = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency — one short-lived session per request."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


async def dispose_engine() -> None:
    await engine.dispose()


def engine_state() -> dict[str, Any]:
    """For /health and leak-canary reporting."""
    pool = engine.pool
    return {
        "size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
    }
