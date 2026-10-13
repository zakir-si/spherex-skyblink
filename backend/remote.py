from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

import requests

from .config import settings

_ALLOWED_HOSTS = {
    "irsa.ipac.caltech.edu",
    "nasa-irsa-spherex.s3.us-east-1.amazonaws.com",
}


def validate_remote_url(url: str) -> str:
    """Allow only known HTTPS SPHEREx archive hosts; reject credentials and custom ports."""
    try:
        parsed = urlparse(url)
        port = parsed.port
    except (TypeError, ValueError) as exc:
        raise ValueError("Malformed archive URL") from exc
    host = (parsed.hostname or "").lower().rstrip(".")
    if parsed.scheme.lower() != "https":
        raise ValueError("Only HTTPS archive URLs are allowed")
    if host not in _ALLOWED_HOSTS:
        raise ValueError("Archive host is not allowlisted")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError("Credentials are not allowed in archive URLs")
    if port not in (None, 443):
        raise ValueError("Non-standard archive ports are not allowed")
    if parsed.fragment:
        raise ValueError("URL fragments are not allowed")
    return url


def is_spherex_onprem_url(url: str) -> bool:
    """True only for IRSA on-prem SPHEREx FITS URLs supporting center/size cutouts."""
    parsed = urlparse(validate_remote_url(url))
    return (
        parsed.hostname == "irsa.ipac.caltech.edu"
        and parsed.path.startswith("/ibe/data/spherex/")
        and parsed.path.lower().endswith((".fits", ".fits.gz", ".fits.fz"))
    )


def add_cutout_params(url: str, ra: float, dec: float, size_deg: float) -> str:
    """Build the supported SPHEREx center/size cutout URL."""
    validate_remote_url(url)
    if not is_spherex_onprem_url(url):
        raise ValueError(
            "This observation is not an IRSA on-prem SPHEREx FITS URL; "
            "the direct center/size cutout API cannot be used for it."
        )
    parsed = urlparse(url)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    q.update({"center": f"{ra:.8f},{dec:.8f}", "size": f"{size_deg:.6f}"})
    return urlunparse(parsed._replace(query=urlencode(q)))


def fetch_bytes(url: str) -> bytes:
    """Fetch a bounded FITS payload without following unvalidated redirects."""
    validate_remote_url(url)
    max_bytes = settings.max_remote_bytes
    with requests.get(
        url,
        timeout=settings.request_timeout_seconds,
        headers={"User-Agent": "SPHEREx-SkyBlink/0.4"},
        stream=True,
        allow_redirects=False,
    ) as response:
        if 300 <= response.status_code < 400:
            raise ValueError("Archive redirected the request; redirect was blocked for safety")
        response.raise_for_status()
        length = response.headers.get("Content-Length")
        if length:
            try:
                if int(length) > max_bytes:
                    raise ValueError(f"Archive product exceeds the {max_bytes // (1024 * 1024)} MB preview limit")
            except ValueError as exc:
                if "preview limit" in str(exc):
                    raise
        chunks: list[bytes] = []
        total = 0
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if not chunk:
                continue
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(f"Archive product exceeds the {max_bytes // (1024 * 1024)} MB preview limit")
            chunks.append(chunk)
        data = b"".join(chunks)
    if not data:
        raise ValueError("IRSA returned an empty response")
    return data
