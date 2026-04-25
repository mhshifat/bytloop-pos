"""Seed demo data for local development.

Creates a demo tenant with a verified owner account, a handful of categories,
products, stock levels across two locations, and a couple of completed orders
so the POS, inventory and orders pages have something to render immediately.

Idempotent by tenant slug — re-running tops up what's missing rather than
duplicating. Safe against production by refusing to run when
``APP_ENV=production``.

Run with:

    uv run -m scripts.seed                 # default demo tenant
    uv run -m scripts.seed --slug acme     # custom slug
    uv run -m scripts.seed --reset         # wipe & re-seed the demo tenant

Never enable on shared/prod databases.
"""

from __future__ import annotations

import argparse
import asyncio
from decimal import Decimal
from uuid import UUID

from sqlalchemy import delete, select

from src.core.config import settings
from src.core.db import async_session_factory
from src.core.security import hash_password
from src.modules.catalog.entity import Category, Product
from src.modules.identity.entity import User
from src.modules.inventory.entity import (
    InventoryLevel,
    Location,
    StockMovement,
    StockMovementKind,
)
from src.modules.sales.entity import Order, OrderItem, OrderStatus, OrderType, Payment
from src.modules.sales.entity import PaymentMethod as PaymentMethodEnum
from src.modules.tenants.entity import Tenant

DEMO_EMAIL = "demo@bytloop.test"
DEMO_PASSWORD = "DemoPass123!"  # local only — never ship to prod
DEMO_TENANT_SLUG_DEFAULT = "demo"


def _money(units: float) -> int:
    return int(round(units * 100))


async def _get_or_create_tenant(session, *, slug: str) -> Tenant:
    existing = (await session.execute(select(Tenant).where(Tenant.slug == slug))).scalar_one_or_none()
    if existing:
        return existing
    tenant = Tenant(
        slug=slug,
        name="Demo Shop",
        country="BD",
        default_currency=settings.currency.default,
        config={},
    )
    session.add(tenant)
    await session.flush()
    return tenant


async def _get_or_create_user(session, *, tenant_id: UUID) -> User:
    existing = (
        await session.execute(
            select(User).where(User.tenant_id == tenant_id, User.email == DEMO_EMAIL)
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    user = User(
        tenant_id=tenant_id,
        email=DEMO_EMAIL,
        first_name="Demo",
        last_name="Owner",
        password_hash=hash_password(DEMO_PASSWORD),
        email_verified=True,
        roles=["owner"],
    )
    session.add(user)
    await session.flush()
    return user


async def _get_or_create_location(
    session, *, tenant_id: UUID, code: str, name: str
) -> Location:
    existing = (
        await session.execute(
            select(Location).where(Location.tenant_id == tenant_id, Location.code == code)
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    loc = Location(tenant_id=tenant_id, code=code, name=name)
    session.add(loc)
    await session.flush()
    return loc


async def _get_or_create_category(
    session, *, tenant_id: UUID, slug: str, name: str
) -> Category:
    existing = (
        await session.execute(
            select(Category).where(Category.tenant_id == tenant_id, Category.slug == slug)
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    cat = Category(tenant_id=tenant_id, slug=slug, name=name)
    session.add(cat)
    await session.flush()
    return cat


async def _get_or_create_product(
    session,
    *,
    tenant_id: UUID,
    sku: str,
    name: str,
    price_units: float,
    category_id: UUID,
    currency: str,
    tax_rate: Decimal = Decimal("0"),
) -> Product:
    existing = (
        await session.execute(
            select(Product).where(Product.tenant_id == tenant_id, Product.sku == sku)
        )
    ).scalar_one_or_none()
    if existing:
        return existing
    product = Product(
        tenant_id=tenant_id,
        sku=sku,
        barcode=None,
        name=name,
        description=None,
        category_id=category_id,
        price_cents=_money(price_units),
        currency=currency,
        is_active=True,
        track_inventory=True,
        tax_rate=tax_rate,
    )
    session.add(product)
    await session.flush()
    return product


async def _ensure_stock(
    session,
    *,
    tenant_id: UUID,
    product_id: UUID,
    location_id: UUID,
    quantity: int,
) -> None:
    existing = (
        await session.execute(
            select(InventoryLevel).where(
                InventoryLevel.tenant_id == tenant_id,
                InventoryLevel.product_id == product_id,
                InventoryLevel.location_id == location_id,
            )
        )
    ).scalar_one_or_none()
    if existing:
        if existing.quantity >= quantity:
            return
        delta = quantity - existing.quantity
        existing.quantity = quantity
    else:
        delta = quantity
        session.add(
            InventoryLevel(
                tenant_id=tenant_id,
                product_id=product_id,
                location_id=location_id,
                quantity=quantity,
                reorder_point=max(5, quantity // 10),
            )
        )
    session.add(
        StockMovement(
            tenant_id=tenant_id,
            product_id=product_id,
            location_id=location_id,
            kind=StockMovementKind.RECEIVE,
            quantity_delta=delta,
        )
    )
    await session.flush()


async def _seed_order(
    session,
    *,
    tenant_id: UUID,
    location_id: UUID,
    cashier_id: UUID,
    currency: str,
    lines: list[tuple[Product, int]],
    number: str,
) -> None:
    existing = (
        await session.execute(
            select(Order).where(Order.tenant_id == tenant_id, Order.number == number)
        )
    ).scalar_one_or_none()
    if existing:
        return
    subtotal = sum(p.price_cents * qty for p, qty in lines)
    order = Order(
        tenant_id=tenant_id,
        location_id=location_id,
        number=number,
        cashier_id=cashier_id,
        order_type=OrderType.RETAIL,
        status=OrderStatus.COMPLETED,
        currency=currency,
        subtotal_cents=subtotal,
        tax_cents=0,
        discount_cents=0,
        total_cents=subtotal,
    )
    session.add(order)
    await session.flush()
    for p, qty in lines:
        line_total = p.price_cents * qty
        session.add(
            OrderItem(
                tenant_id=tenant_id,
                order_id=order.id,
                product_id=p.id,
                name_snapshot=p.name,
                unit_price_cents=p.price_cents,
                quantity=qty,
                subtotal_cents=line_total,
                tax_cents=0,
                line_total_cents=line_total,
            )
        )
    session.add(
        Payment(
            tenant_id=tenant_id,
            order_id=order.id,
            method=PaymentMethodEnum.CASH,
            amount_cents=subtotal,
            currency=currency,
        )
    )
    await session.flush()


async def _reset_tenant(session, *, tenant_id: UUID) -> None:
    # Deletes cascade from tenants.id, but we wipe the tenant root directly.
    await session.execute(delete(StockMovement).where(StockMovement.tenant_id == tenant_id))
    await session.execute(delete(InventoryLevel).where(InventoryLevel.tenant_id == tenant_id))
    await session.execute(delete(OrderItem).where(OrderItem.tenant_id == tenant_id))
    await session.execute(delete(Payment).where(Payment.tenant_id == tenant_id))
    await session.execute(delete(Order).where(Order.tenant_id == tenant_id))
    await session.execute(delete(Product).where(Product.tenant_id == tenant_id))
    await session.execute(delete(Category).where(Category.tenant_id == tenant_id))
    await session.execute(delete(Location).where(Location.tenant_id == tenant_id))
    await session.execute(delete(User).where(User.tenant_id == tenant_id))
    await session.execute(delete(Tenant).where(Tenant.id == tenant_id))
    await session.flush()


async def seed(*, slug: str, reset: bool) -> None:
    if settings.app.env == "production":
        raise SystemExit("Refusing to seed into APP_ENV=production.")

    currency = settings.currency.default

    async with async_session_factory() as session:
        if reset:
            existing = (
                await session.execute(select(Tenant).where(Tenant.slug == slug))
            ).scalar_one_or_none()
            if existing:
                await _reset_tenant(session, tenant_id=existing.id)
                await session.commit()

        tenant = await _get_or_create_tenant(session, slug=slug)
        user = await _get_or_create_user(session, tenant_id=tenant.id)
        main = await _get_or_create_location(
            session, tenant_id=tenant.id, code="main", name="Main warehouse"
        )
        shop = await _get_or_create_location(
            session, tenant_id=tenant.id, code="shop", name="Storefront"
        )

        beverages = await _get_or_create_category(
            session, tenant_id=tenant.id, slug="beverages", name="Beverages"
        )
        snacks = await _get_or_create_category(
            session, tenant_id=tenant.id, slug="snacks", name="Snacks"
        )
        groceries = await _get_or_create_category(
            session, tenant_id=tenant.id, slug="groceries", name="Groceries"
        )

        catalog_rows: list[tuple[str, str, float, UUID]] = [
            ("TEA-001", "Green tea 100g", 4.50, beverages.id),
            ("COF-001", "Arabica coffee 250g", 12.00, beverages.id),
            ("WAT-001", "Mineral water 1L", 0.80, beverages.id),
            ("CHI-001", "Crisps 150g", 2.20, snacks.id),
            ("CHO-001", "Milk chocolate bar", 1.50, snacks.id),
            ("RIC-001", "Basmati rice 5kg", 18.00, groceries.id),
            ("OIL-001", "Sunflower oil 1L", 3.80, groceries.id),
            ("SUG-001", "White sugar 1kg", 1.20, groceries.id),
        ]
        products: list[Product] = []
        for sku, name, price, cat_id in catalog_rows:
            p = await _get_or_create_product(
                session,
                tenant_id=tenant.id,
                sku=sku,
                name=name,
                price_units=price,
                category_id=cat_id,
                currency=currency,
            )
            products.append(p)

        for p in products:
            await _ensure_stock(
                session, tenant_id=tenant.id, product_id=p.id, location_id=main.id, quantity=80
            )
            await _ensure_stock(
                session, tenant_id=tenant.id, product_id=p.id, location_id=shop.id, quantity=12
            )

        await _seed_order(
            session,
            tenant_id=tenant.id,
            location_id=shop.id,
            cashier_id=user.id,
            currency=currency,
            number="SO-DEMO-0001",
            lines=[(products[0], 2), (products[3], 1)],
        )
        await _seed_order(
            session,
            tenant_id=tenant.id,
            location_id=shop.id,
            cashier_id=user.id,
            currency=currency,
            number="SO-DEMO-0002",
            lines=[(products[5], 1), (products[6], 2)],
        )

        await session.commit()

    print(f"Seeded tenant '{slug}'. Sign in with {DEMO_EMAIL} / {DEMO_PASSWORD}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed demo data.")
    parser.add_argument("--slug", default=DEMO_TENANT_SLUG_DEFAULT)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()
    asyncio.run(seed(slug=args.slug, reset=args.reset))


if __name__ == "__main__":
    main()
