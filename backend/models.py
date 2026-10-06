from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class Observation(BaseModel):
    obs_id: str
    collection: str
    ra: float | None = None
    dec: float | None = None
    start_mjd: float | None = None
    end_mjd: float | None = None
    wavelength_min_m: float | None = None
    wavelength_max_m: float | None = None
    access_url: str | None = None
    access_format: str | None = None
    estimated_size_kb: int | None = None


class SearchResponse(BaseModel):
    source: str
    query: dict
    observations: list[Observation]


class DemoFrame(BaseModel):
    id: str
    timestamp: datetime
    label: str
    image_data_url: str
    candidate_count: int = 0


class Candidate(BaseModel):
    id: str
    x: float
    y: float
    dx: float
    dy: float
    motion_px: float
    snr: float
    score: float
    kind: str


class DemoResponse(BaseModel):
    frames: list[DemoFrame]
    candidates: list[Candidate]
    spectrum_wavelength_um: list[float]
    spectrum_flux_ujy: list[float]


class SearchQuery(BaseModel):
    ra: float = Field(..., ge=0, le=360)
    dec: float = Field(..., ge=-90, le=90)
    radius_deg: float = Field(0.05, gt=0, le=1.0)
    wavelength_um: float | None = Field(default=None, gt=0, le=10)

    @field_validator("radius_deg")
    @classmethod
    def finite_radius(cls, value: float) -> float:
        if not float(value) == value:
            raise ValueError("radius must be finite")
        return value
