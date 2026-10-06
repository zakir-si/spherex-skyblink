from __future__ import annotations

import csv
import io
from typing import Any

import requests

from .config import settings
from .models import Observation


def _to_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _first(row: dict[str, str], *names: str) -> str | None:
    lowered = {str(k).lower(): v for k, v in row.items()}
    for name in names:
        if name.lower() in lowered:
            return lowered[name.lower()]
    return None


def parse_sia_csv(text: str, collection: str) -> list[Observation]:
    reader = csv.DictReader(io.StringIO(text))
    result: list[Observation] = []
    for i, row in enumerate(reader):
        obs_id = _first(row, "obs_id", "obs_publisher_did", "ID") or f"row-{i}"
        result.append(Observation(
            obs_id=str(obs_id),
            collection=_first(row, "obs_collection") or collection,
            ra=_to_float(_first(row, "s_ra", "ra")),
            dec=_to_float(_first(row, "s_dec", "dec")),
            start_mjd=_to_float(_first(row, "t_min")),
            end_mjd=_to_float(_first(row, "t_max")),
            wavelength_min_m=_to_float(_first(row, "em_min")),
            wavelength_max_m=_to_float(_first(row, "em_max")),
            access_url=_first(row, "access_url", "getdataurl", "url"),
            access_format=_first(row, "access_format"),
            estimated_size_kb=_to_int(_first(row, "access_estsize")),
        ))
    return result


def search_spherex(ra: float, dec: float, radius_deg: float, wavelength_um: float | None = None) -> list[Observation]:
    params: dict[str, str | float] = {
        "COLLECTION": settings.spherex_collection,
        "POS": f"CIRCLE {ra} {dec} {radius_deg}",
        "DPTYPE": "image",
        "CALIB": "2",
        "FORMAT": "image/fits",
        "MAXREC": str(settings.max_results),
        "RESPONSEFORMAT": "CSV",
    }
    if wavelength_um is not None:
        params["BAND"] = f"{wavelength_um * 1e-6}"

    response = requests.get(settings.irsa_sia_url, params=params, timeout=settings.request_timeout_seconds)
    if response.status_code >= 400 and settings.spherex_collection == "spherex_qr3":
        fallback = dict(params)
        fallback["COLLECTION"] = "spherex_qr2"
        fallback_response = requests.get(settings.irsa_sia_url, params=fallback, timeout=settings.request_timeout_seconds)
        fallback_response.raise_for_status()
        return parse_sia_csv(fallback_response.text, "spherex_qr2")[: settings.max_results]
    response.raise_for_status()
    return parse_sia_csv(response.text, settings.spherex_collection)[: settings.max_results]
