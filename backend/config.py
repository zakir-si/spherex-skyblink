from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    irsa_sia_url: str = os.getenv("IRSA_SIA_URL", "https://irsa.ipac.caltech.edu/SIA")
    spherex_collection: str = os.getenv("SPHEREX_COLLECTION", "spherex_qr3")
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))
    max_search_radius_deg: float = float(os.getenv("MAX_SEARCH_RADIUS_DEG", "1.0"))
    # Metadata results are cheap; previews are deliberately capped separately.
    max_results: int = int(os.getenv("MAX_RESULTS", "100"))
    max_live_previews: int = int(os.getenv("MAX_LIVE_PREVIEWS", "6"))
    preview_size_deg: float = float(os.getenv("PREVIEW_SIZE_DEG", "0.05"))
    preview_cache_size: int = int(os.getenv("PREVIEW_CACHE_SIZE", "64"))


settings = Settings()
