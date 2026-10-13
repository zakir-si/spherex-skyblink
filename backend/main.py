from __future__ import annotations

from functools import lru_cache
import math
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import settings
from .demo import build_demo
from .fits_preview import fits_bytes_to_preview
from .irsa import search_spherex
from .models import SearchResponse
from .remote import add_cutout_params, fetch_bytes, validate_remote_url

app = FastAPI(title="SPHEREx SkyBlink API", version="0.3.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    try:
        import astropy  # noqa: F401
        science_ready = True
    except ImportError:
        science_ready = False

    return {
        "status": "ok",
        "service": "spherex-skyblink",
        "collection": settings.spherex_collection,
        "science_ready": science_ready,
        "max_live_previews": settings.max_live_previews,
        "max_remote_bytes": settings.max_remote_bytes,
        "preview_cache_entries": _cached_preview.cache_info().currsize,
    }


@app.get("/api/demo")
def demo():
    return build_demo()


@app.get("/api/search", response_model=SearchResponse)
def search(
    ra: float = Query(..., ge=0, le=360),
    dec: float = Query(..., ge=-90, le=90),
    radius_deg: float = Query(0.05, gt=0, le=1.0),
    wavelength_um: float | None = Query(None, gt=0, le=10),
):
    if not all(math.isfinite(v) for v in (ra, dec, radius_deg)) or (wavelength_um is not None and not math.isfinite(wavelength_um)):
        raise HTTPException(status_code=422, detail="Coordinates, radius, and wavelength must be finite numbers.")
    if radius_deg > settings.max_search_radius_deg:
        raise HTTPException(status_code=422, detail=f"Search radius cannot exceed {settings.max_search_radius_deg} degrees.")
    try:
        rows = search_spherex(ra, dec, radius_deg, wavelength_um)
    except Exception as exc:
        # Log full details server-side in a production deployment; keep public errors bounded.
        raise HTTPException(status_code=502, detail="IRSA archive query failed. Please retry shortly.") from exc

    return SearchResponse(
        source="IRSA SIA v2",
        query={"ra": ra, "dec": dec, "radius_deg": radius_deg, "wavelength_um": wavelength_um},
        observations=rows,
    )


@lru_cache(maxsize=settings.preview_cache_size)
def _cached_preview(url: str, ra: float, dec: float, size_deg: float) -> str:
    cutout_url = add_cutout_params(url, ra, dec, size_deg)
    data = fetch_bytes(cutout_url)
    return fits_bytes_to_preview(data)


@app.get("/api/preview")
def preview(
    url: str = Query(..., min_length=12),
    ra: float = Query(..., ge=0, le=360),
    dec: float = Query(..., ge=-90, le=90),
    size_deg: float = Query(settings.preview_size_deg, gt=0, le=0.5),
):
    try:
        validate_remote_url(url)
        image_data_url = _cached_preview(url, round(ra, 8), round(dec, 8), round(size_deg, 6))
        cutout_url = add_cutout_params(url, ra, dec, size_deg)
        return {"image_data_url": image_data_url, "source_url": cutout_url, "cached": True}
    except ImportError as exc:
        raise HTTPException(
            status_code=503,
            detail="Live FITS previews require Astropy. Reinstall backend/requirements.txt.",
        ) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Preview could not be prepared: {str(exc)[:240]}") from exc


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
