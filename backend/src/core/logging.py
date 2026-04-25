"""structlog configuration.

Pretty console in dev · JSON to stdout in prod. The correlation-ID contextvar
is attached to every log line automatically.
"""

from __future__ import annotations

import logging
import sys

import structlog

from src.core.config import settings
from src.core.correlation import _correlation_id


def _add_correlation_id(_: object, __: str, event_dict: dict[str, object]) -> dict[str, object]:
    cid = _correlation_id.get()
    if cid:
        event_dict.setdefault("correlation_id", cid)
    return event_dict


def configure_logging() -> None:
    level = getattr(logging, settings.observability.log_level.upper(), logging.INFO)

    shared_processors: list[structlog.typing.Processor] = [
        structlog.contextvars.merge_contextvars,
        _add_correlation_id,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if settings.observability.log_renderer == "json":
        renderer: structlog.typing.Processor = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    structlog.configure(
        processors=[*shared_processors, renderer],
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Redirect stdlib logging (uvicorn, sqlalchemy, etc.) through structlog.
    logging.basicConfig(level=level, handlers=[], format="%(message)s")
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(name).handlers.clear()
        logging.getLogger(name).propagate = True
