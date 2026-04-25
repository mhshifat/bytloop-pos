"""Alembic environment — async-aware."""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine

from src.core.config import settings
from src.core.db import Base, get_asyncpg_connection_settings

# Ensure every module's entities are imported so Base.metadata is complete.
# As modules are added, import them here.
# ruff: noqa: F401
from src.modules.audit import entity as _audit_entity
from src.modules.catalog import entity as _catalog_entity
from src.modules.customers import entity as _customers_entity
from src.modules.discounts import entity as _discounts_entity
from src.modules.identity import entity as _identity_entity
from src.modules.inventory import entity as _inventory_entity
from src.modules.procurement import entity as _procurement_entity
from src.modules.sales import entity as _sales_entity
from src.modules.shifts import entity as _shifts_entity
from src.modules.tax import entity as _tax_entity
from src.modules.tenants import entity as _tenant_entity
from src.verticals.fnb.restaurant import entity as _restaurant_entity
from src.verticals.hospitality.hotel import entity as _hotel_entity
from src.verticals.retail.apparel import entity as _apparel_entity
from src.verticals.retail.grocery import entity as _grocery_entity
from src.verticals.services.garage import entity as _garage_entity
from src.verticals.services.gym import entity as _gym_entity
from src.verticals.services.salon import entity as _salon_entity
from src.verticals.specialty.cinema import entity as _cinema_entity
from src.verticals.specialty.jewelry import entity as _jewelry_entity
from src.verticals.specialty.pharmacy import entity as _pharmacy_entity
from src.verticals.specialty.rental import entity as _rental_entity


config = context.config
_alembic_url, _alembic_connect_args = get_asyncpg_connection_settings(
    settings.database.url,
)
config.set_main_option("sqlalchemy.url", _alembic_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=_alembic_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    connectable = create_async_engine(
        _alembic_url,
        connect_args=_alembic_connect_args,
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
