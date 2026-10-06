from __future__ import annotations

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

app = FastAPI(title="SPHEREx SkyBlink API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": "spherex-skyblink", "collection": settings.spherex_collection}


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
    try:
        rows = search_spherex(ra, dec, radius_deg, wavelength_um)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"IRSA query failed: {exc}") from exc
    return SearchResponse(
        source="IRSA SIA v2",
        query={"ra": ra, "dec": dec, "radius_deg": radius_deg, "wavelength_um": wavelength_um},
        observations=rows,
    )


@app.get("/api/preview")
def preview(
    url: str = Query(..., min_length=12),
    ra: float = Query(..., ge=0, le=360),
    dec: float = Query(..., ge=-90, le=90),
    size_deg: float = Query(0.05, gt=0, le=0.5),
):
    try:
        validate_remote_url(url)
        cutout_url = add_cutout_params(url, ra, dec, size_deg)
        data = fetch_bytes(cutout_url)
        return {"image_data_url": fits_bytes_to_preview(data), "source_url": cutout_url}
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Preview failed: {exc}") from exc


FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
