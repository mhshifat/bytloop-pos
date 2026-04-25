"""Shared Pydantic base classes.

All API I/O schemas inherit from ``CamelModel`` so payloads are camelCase over
the wire while internals stay snake_case (Python convention). See docs/PLAN.md §5.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base for every request/response schema."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
        str_strip_whitespace=True,
    )
