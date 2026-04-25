from __future__ import annotations

from uuid import UUID

from pydantic import EmailStr, Field

from src.core.schemas import CamelModel


class CustomerRead(CamelModel):
    id: UUID
    first_name: str
    last_name: str
    email: EmailStr | None
    phone: str | None
    notes: str | None


class CustomerCreate(CamelModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str = ""
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None


class CustomerUpdate(CamelModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    notes: str | None = None


class CustomerList(CamelModel):
    items: list[CustomerRead]
    has_more: bool
    page: int
    page_size: int
