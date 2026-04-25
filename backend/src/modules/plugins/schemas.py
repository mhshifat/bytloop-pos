from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import Field

from src.core.schemas import CamelModel


class PluginMetaRead(CamelModel):
    code: str
    name: str
    description: str
    version: str
    hooks: list[str]


class PluginInstallRead(CamelModel):
    id: UUID
    code: str
    enabled: bool
    config: dict[str, Any]
    installed_at: datetime


class PluginInstallRequest(CamelModel):
    code: str = Field(min_length=1, max_length=64)
    enabled: bool = True
    config: dict[str, Any] | None = None


class PluginToggleRequest(CamelModel):
    enabled: bool
