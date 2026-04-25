"""Trusted real client IP extraction.

We do NOT blindly trust X-Forwarded-For, because any direct client can spoof it.
Instead, we only honor proxy headers when the immediate peer IP is within an
explicit allowlist of trusted proxy CIDRs.
"""

from __future__ import annotations

import ipaddress
from collections.abc import Iterable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from src.core.config import settings


def _parse_networks(cidrs: Iterable[str]) -> list[ipaddress._BaseNetwork]:  # type: ignore[name-defined]
    networks: list[ipaddress._BaseNetwork] = []  # type: ignore[name-defined]
    for raw in cidrs:
        try:
            networks.append(ipaddress.ip_network(raw, strict=False))
        except ValueError:
            continue
    return networks


_TRUSTED_PROXY_NETWORKS = _parse_networks(settings.app.trusted_proxy_cidrs)


def _ip_in_trusted_proxies(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in net for net in _TRUSTED_PROXY_NETWORKS)


def get_real_ip(request: Request) -> str:
    """Return the best-effort real client IP for this request."""
    peer = request.client.host if request.client else "unknown"
    if not settings.app.trust_proxy_headers:
        return peer
    if not _ip_in_trusted_proxies(peer):
        # Direct-to-app request (or unknown proxy). Do not trust headers.
        return peer

    xff = request.headers.get("x-forwarded-for")
    if xff:
        # XFF is "client, proxy1, proxy2". We want the original client.
        first = xff.split(",", 1)[0].strip()
        if first:
            return first

    # Fallbacks for some proxies
    rip = request.headers.get("x-real-ip")
    if rip:
        return rip.strip() or peer

    return peer


class RealIpMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        request.state.real_ip = get_real_ip(request)
        response: Response = await call_next(request)
        return response

