"""Tenant entity — the business account boundary.

Every other table in the system carries ``tenant_id`` and joins to this row
for row-level isolation. See docs/PLAN.md §3.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from src.core.db import Base


class VerticalProfile(StrEnum):
    """The operator's business type — drives UX mode, not row-level schema.

    Each profile unlocks a variant of the POS without needing its own module.
    "retail_general" is the baseline; swap to a specific one and the POS
    hides irrelevant buttons, adjusts labels, and exposes vertical-specific
    add-ons.
    """

    RETAIL_GENERAL = "retail_general"
    RETAIL_ELECTRONICS = "retail_electronics"
    RETAIL_APPAREL = "retail_apparel"
    RETAIL_GROCERY = "retail_grocery"
    RETAIL_PHARMACY = "retail_pharmacy"
    RETAIL_JEWELRY = "retail_jewelry"
    RETAIL_FURNITURE = "retail_furniture"
    RETAIL_BOOKSTORE = "retail_bookstore"
    RETAIL_LIQUOR = "retail_liquor"
    RETAIL_CANNABIS = "retail_cannabis"
    RETAIL_FLORIST = "retail_florist"
    RETAIL_THRIFT = "retail_thrift"
    RETAIL_PET_STORE = "retail_pet_store"
    RETAIL_HARDWARE = "retail_hardware"
    RETAIL_DEPARTMENT = "retail_department"

    FNB_RESTAURANT = "fnb_restaurant"
    FNB_QSR = "fnb_qsr"
    FNB_CAFE = "fnb_cafe"
    FNB_BAR = "fnb_bar"
    FNB_FOOD_TRUCK = "fnb_food_truck"
    FNB_BAKERY = "fnb_bakery"
    FNB_PIZZA = "fnb_pizza"
    FNB_CLOUD_KITCHEN = "fnb_cloud_kitchen"
    FNB_CAFETERIA = "fnb_cafeteria"

    HOSPITALITY_HOTEL = "hospitality_hotel"
    HOSPITALITY_RESORT = "hospitality_resort"
    HOSPITALITY_SALON = "hospitality_salon"
    HOSPITALITY_EVENT = "hospitality_event"
    HOSPITALITY_THEME_PARK = "hospitality_theme_park"

    SERVICES_GARAGE = "services_garage"
    SERVICES_GAS_STATION = "services_gas_station"
    SERVICES_CAR_WASH = "services_car_wash"
    SERVICES_LAUNDRY = "services_laundry"
    SERVICES_GYM = "services_gym"
    SERVICES_MEDICAL = "services_medical"
    SERVICES_VETERINARY = "services_veterinary"

    SPECIALTY_MUSEUM = "specialty_museum"
    SPECIALTY_CINEMA = "specialty_cinema"
    SPECIALTY_WHOLESALE = "specialty_wholesale"
    SPECIALTY_RENTAL = "specialty_rental"
    SPECIALTY_MARKET = "specialty_market"
    SPECIALTY_NONPROFIT = "specialty_nonprofit"


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid(), init=False
    )
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(2), default="BD")
    default_currency: Mapped[str] = mapped_column(String(3), default="BDT")
    vertical_profile: Mapped[VerticalProfile] = mapped_column(
        String(32), default=VerticalProfile.RETAIL_GENERAL
    )

    # Whitelisted per-tenant overrides of global config (docs/PLAN.md §4a).
    config: Mapped[dict[str, Any]] = mapped_column(JSONB, default_factory=dict)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), init=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )


class TenantHelpers:
    """Dedicated helpers per docs/PLAN.md §6 (one helper class per entity)."""

    @staticmethod
    def resolved_currency(tenant: Tenant) -> str:
        override = tenant.config.get("default_currency") if tenant.config else None
        if isinstance(override, str) and len(override) == 3:
            return override.upper()
        return tenant.default_currency
