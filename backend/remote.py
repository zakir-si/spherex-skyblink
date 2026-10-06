from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

from .config import settings

_ALLOWED_HOST_SUFFIXES = ("irsa.ipac.caltech.edu", "amazonaws.com")
_ALLOWED_SPHEREX_BUCKET = "nasa-irsa-spherex.s3.us-east-1.amazonaws.com"


def validate_remote_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("Only HTTPS archive URLs are allowed")
    host = (parsed.hostname or "").lower()
    if host != _ALLOWED_SPHEREX_BUCKET and not any(host == suffix or host.endswith("." + suffix) for suffix in _ALLOWED_HOST_SUFFIXES):
        raise ValueError("Archive host is not allowlisted")
    return url


def add_cutout_params(url: str, ra: float, dec: float, size_deg: float) -> str:
    """Build an IRSA cutout URL while preserving existing query parameters."""
    validate_remote_url(url)
    parsed = urlparse(url)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    q.update({"center": f"{ra:.8f},{dec:.8f}", "size": f"{size_deg:.6f}"})
    return urlunparse(parsed._replace(query=urlencode(q)))


def fetch_bytes(url: str) -> bytes:
    validate_remote_url(url)
    r = requests.get(url, timeout=settings.request_timeout_seconds,
                     headers={"User-Agent": "SPHEREx-SkyBlink/0.1"})
    r.raise_for_status()
    return r.content
