"""Async SQLAlchemy engine + session factory.

Pool sized per docs/PLAN.md §15b. Fast pool timeout so a saturated Neon free
tier surfaces as a ``RateLimitError`` instead of a hung request.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, MappedAsDataclass

from src.core.config import settings

# libpq connection-URI options that get forwarded as ``connect()`` kwargs by
# SQLAlchemy but are not valid for asyncpg (or are handled elsewhere).
# See: https://www.postgresql.org/docs/current/libpq-connect.html#LIBPQ-PARAMKEYWORDS
_LIBPQ_QUERY_PARAMS_DROP: frozenset[str] = frozenset(
    {
        "channel_binding",
        "gssencmode",
    }
)


def _to_asyncpg_scheme(url: str) -> str:
    """Use asyncpg — bare ``postgresql://`` would make SQLAlchemy try psycopg2 (not a dep)."""
    if url.startswith("postgresql://") and not url.startswith("postgresql+"):
        return "postgresql+asyncpg://" + url.removeprefix("postgresql://")
    return url


def get_asyncpg_connection_settings(url: str) -> tuple[str, dict[str, Any]]:
    """Build async DSN and ``connect_args`` for asyncpg.

    libpq query params like ``sslmode`` are not valid for asyncpg's
    ``connect()`` and are stripped; SSL intent is mapped to ``ssl=`` instead.
    """
    dsn = _to_asyncpg_scheme(url)
    parsed = urlparse(dsn)
    connect_args: dict[str, Any] = {}
    new_qsl: list[tuple[str, str]] = []
    ssl_mode: str | None = None
    for k, v in parse_qsl(parsed.query, keep_blank_values=True):
        if k == "sslmode":
            ssl_mode = v
            continue
        if k in _LIBPQ_QUERY_PARAMS_DROP:
            continue
        new_qsl.append((k, v))
    if ssl_mode is not None:
        mode = ssl_mode.lower()
        if mode in ("require", "verify-ca", "verify-full"):
            connect_args["ssl"] = True
        elif mode == "disable":
            connect_args["ssl"] = False
        # allow / prefer: no explicit ssl; asyncpg uses its own defaults
    new_query = urlencode(new_qsl, doseq=True)
    clean = urlunparse(
        (parsed.scheme, parsed.netloc, parsed.path, "", new_query, parsed.fragment),
    )
    return clean, connect_args


def _async_database_url(url: str) -> str:
    """Back-compat: DSN only (use :func:`get_asyncpg_connection_settings` for full picture)."""
    return get_asyncpg_connection_settings(url)[0]


class Base(MappedAsDataclass, DeclarativeBase):
    """Project-wide declarative base. snake_case tables + columns."""


def _build_engine() -> AsyncEngine:
    url, connect_args = get_asyncpg_connection_settings(settings.database.url)
    return create_async_engine(
        url,
        connect_args=connect_args,
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
