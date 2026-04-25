from __future__ import annotations

from uuid import UUID

from src.core.schemas import CamelModel


class BookLookupResult(CamelModel):
    """Minimal product shape returned by the ISBN lookup endpoint."""

    id: UUID
    name: str
    sku: str
    price_cents: int
    currency: str
