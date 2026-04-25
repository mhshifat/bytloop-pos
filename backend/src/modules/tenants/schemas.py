from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class TenantRead(CamelModel):
    id: UUID
    slug: str
    name: str
    country: str
    default_currency: str
    vertical_profile: str = "retail_general"
    config: dict[str, Any]


class TenantUpdate(CamelModel):
    name: str | None = Field(default=None, max_length=255)
    country: str | None = Field(default=None, min_length=2, max_length=2)
    default_currency: str | None = Field(default=None, min_length=3, max_length=3)
    vertical_profile: str | None = Field(default=None, max_length=32)


class TenantBrandUpdate(CamelModel):
    """Whitelisted writeable subset of ``tenant.config.brand``.

    Stored as a sub-object rather than top-level columns so we can ship new
    knobs (badge shape, font pairing, etc.) without a migration per change.
    """

    logo_url: str | None = Field(default=None, max_length=512)
    primary_color: str | None = Field(default=None, pattern=r"^#(?:[0-9a-fA-F]{3}){1,2}$")
    accent_color: str | None = Field(default=None, pattern=r"^#(?:[0-9a-fA-F]{3}){1,2}$")
    receipt_header: str | None = Field(default=None, max_length=255)
    receipt_footer: str | None = Field(default=None, max_length=512)


class TenantBrandRead(CamelModel):
    logo_url: str | None = None
    primary_color: str | None = None
    accent_color: str | None = None
    receipt_header: str | None = None
    receipt_footer: str | None = None
