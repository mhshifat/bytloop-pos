"""Email adapter abstraction — Strategy pattern (docs/PLAN.md §6)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EmailMessage:
    to: str
    subject: str
    html: str
    text: str | None = None

    def plain_text(self) -> str:
        return self.text or _strip_tags(self.html)


class EmailAdapter(ABC):
    """Abstract email provider.

    Every provider (SMTP, Mailgun, SendGrid, ...) implements this interface.
    Services depend on ``EmailAdapter``, never on a concrete class.
    """

    @abstractmethod
    async def send(self, message: EmailMessage) -> None: ...


def _strip_tags(html: str) -> str:
    out: list[str] = []
    inside = False
    for ch in html:
        if ch == "<":
            inside = True
            continue
        if ch == ">":
            inside = False
            continue
        if not inside:
            out.append(ch)
    return "".join(out).strip()
