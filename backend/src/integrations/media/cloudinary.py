from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

import httpx

from src.core.config import settings


MAX_UPLOAD_BYTES = 95 * 1024 * 1024


@dataclass(frozen=True)
class SignedUpload:
    upload_url: str
    fields: dict[str, str]
    public_id: str


def is_configured() -> bool:
    c = settings.cloudinary
    return bool(c.cloud_name and c.api_key and c.api_secret.get_secret_value())


def _signature(params: dict[str, str]) -> str:
    """Cloudinary signature: SHA1 of sorted params + api_secret."""
    secret = settings.cloudinary.api_secret.get_secret_value()
    to_sign = "&".join(f"{k}={v}" for k, v in sorted(params.items())) + secret
    return hashlib.sha1(to_sign.encode("utf-8")).hexdigest()


def signed_direct_upload(*, folder: str, public_id: str, tags: list[str]) -> SignedUpload:
    ts = str(int(time.time()))
    base_params = {
        "folder": folder,
        "public_id": public_id,
        "resource_type": "image",
        "tags": ",".join(tags),
        "timestamp": ts,
    }
    # Signature excludes file itself.
    sig_params = {k: v for k, v in base_params.items() if k != "resource_type"}
    signature = _signature(sig_params)
    fields = {
        "api_key": settings.cloudinary.api_key,
        "timestamp": ts,
        "signature": signature,
        "folder": folder,
        "public_id": public_id,
        "tags": ",".join(tags),
    }
    upload_url = f"https://api.cloudinary.com/v1_1/{settings.cloudinary.cloud_name}/image/upload"
    return SignedUpload(upload_url=upload_url, fields=fields, public_id=public_id)


async def destroy(*, public_id: str) -> bool:
    """Delete an asset by public_id. Returns False on failure."""
    if not is_configured():
        return False
    ts = str(int(time.time()))
    sig = _signature({"public_id": public_id, "timestamp": ts})
    url = f"https://api.cloudinary.com/v1_1/{settings.cloudinary.cloud_name}/image/destroy"
    data = {
        "public_id": public_id,
        "timestamp": ts,
        "api_key": settings.cloudinary.api_key,
        "signature": sig,
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(url, data=data)
            return r.status_code == 200
    except Exception:  # noqa: BLE001
        return False


async def fetch_ocr_text(*, public_id: str) -> str | None:
    """Fetch OCR text for an uploaded image via Cloudinary OCR add-on.

    Requires the Cloudinary account to have OCR enabled (e.g. adv_ocr).
    Returns None if not available or on failure.
    """
    if not is_configured():
        return None
    url = (
        f"https://api.cloudinary.com/v1_1/{settings.cloudinary.cloud_name}"
        f"/resources/image/upload/{public_id}"
    )
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                url,
                params={"ocr": "adv_ocr"},
                auth=(settings.cloudinary.api_key, settings.cloudinary.api_secret.get_secret_value()),
            )
        if r.status_code != 200:
            return None
        data = r.json()
        info = data.get("info") if isinstance(data, dict) else None
        ocr = info.get("ocr") if isinstance(info, dict) else None
        adv = ocr.get("adv_ocr") if isinstance(ocr, dict) else None
        blocks = adv.get("data") if isinstance(adv, dict) else None
        if not isinstance(blocks, list):
            return None
        texts: list[str] = []
        for b in blocks:
            if isinstance(b, dict) and isinstance(b.get("text"), str):
                texts.append(b["text"])
        out = "\n".join(t.strip() for t in texts if t.strip()).strip()
        return out or None
    except Exception:  # noqa: BLE001
        return None


async def fetch_tags(*, public_id: str) -> list[str] | None:
    """Fetch auto-tags (categorization) for an image.

    Requires Cloudinary categorization add-on (e.g. google_tagging) to be enabled.
    """
    if not is_configured():
        return None
    url = (
        f"https://api.cloudinary.com/v1_1/{settings.cloudinary.cloud_name}"
        f"/resources/image/upload/{public_id}"
    )
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(
                url,
                params={"categorization": "google_tagging"},
                auth=(settings.cloudinary.api_key, settings.cloudinary.api_secret.get_secret_value()),
            )
        if r.status_code != 200:
            return None
        data = r.json()
        info = data.get("info") if isinstance(data, dict) else None
        categ = info.get("categorization") if isinstance(info, dict) else None
        gt = categ.get("google_tagging") if isinstance(categ, dict) else None
        tags = gt.get("data") if isinstance(gt, dict) else None
        if not isinstance(tags, list):
            return None
        out: list[str] = []
        for t in tags:
            if isinstance(t, dict) and isinstance(t.get("tag"), str):
                out.append(t["tag"])
        return out or None
    except Exception:  # noqa: BLE001
        return None

