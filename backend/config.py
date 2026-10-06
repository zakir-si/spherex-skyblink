from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    irsa_sia_url: str = os.getenv("IRSA_SIA_URL", "https://irsa.ipac.caltech.edu/SIA")
    spherex_collection: str = os.getenv("SPHEREX_COLLECTION", "spherex_qr3")
    request_timeout_seconds: float = float(os.getenv("REQUEST_TIMEOUT_SECONDS", "30"))
    max_search_radius_deg: float = float(os.getenv("MAX_SEARCH_RADIUS_DEG", "1.0"))
    max_results: int = int(os.getenv("MAX_RESULTS", "200"))


settings = Settings()
