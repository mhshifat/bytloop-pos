"""Apparel — variant matrix bulk creation."""

from __future__ import annotations

import pytest

from src.modules.catalog.entity import Product
from src.modules.catalog.repository import ProductRepository
from src.modules.tenants.repository import TenantRepository
from src.verticals.retail.apparel.service import ApparelService


@pytest.mark.asyncio
async def test_bulk_create_generates_full_matrix(db_session):
    tenant = await TenantRepository(db_session).create(
        slug="a1", name="A", country="BD", default_currency="BDT"
    )
    product = Product(
        tenant_id=tenant.id,
        sku="TSHIRT",
        barcode=None,
        name="T-shirt",
        description=None,
        category_id=None,
        price_cents=1500,
        currency="BDT",
        is_active=True,
        track_inventory=True,
        tax_rate=0,  # type: ignore[arg-type]
        vertical_data={},
    )
    await ProductRepository(db_session).add(product)

    service = ApparelService(db_session)
    variants = await service.bulk_create(
        tenant_id=tenant.id,
        product_id=product.id,
        sizes=["S", "M", "L"],
        colors=["BLACK", "WHITE"],
        sku_prefix="TEE",
    )

    assert len(variants) == 6  # 3 sizes * 2 colors
    skus = {v.sku for v in variants}
    assert "TEE-S-BLACK" in skus
    assert "TEE-L-WHITE" in skus

    from_repo = await service.list_for_product(
        tenant_id=tenant.id, product_id=product.id
    )
    assert len(from_repo) == 6
