from __future__ import annotations

import base64
import io
import math

import numpy as np
from PIL import Image

_MAX_PREVIEW_PIXELS = 4_000_000
_MAX_FITS_PLANE_PIXELS = 40_000_000
_SCIENCE_EXTENSIONS = {"SCI", "SCIENCE", "IMAGE", "FLUX", "INTENSITY", "PRIMARY"}


def _png(array: np.ndarray) -> str:
    x = np.asarray(array, dtype=float)
    if x.ndim != 2 or not x.size:
        raise ValueError("Preview data must be a non-empty 2D image")
    # Keep normalization and PNG encoding bounded even if a large array reaches here.
    if x.size > _MAX_PREVIEW_PIXELS:
        stride = math.ceil(math.sqrt(x.size / _MAX_PREVIEW_PIXELS))
        x = x[::stride, ::stride]
    finite = np.isfinite(x)
    if not finite.any():
        raise ValueError("FITS extension contains no finite pixels")

    lo, hi = np.percentile(x[finite], [1, 99.7])
    if not np.isfinite(lo) or not np.isfinite(hi):
        raise ValueError("FITS extension has invalid percentile statistics")

    span = max(float(hi - lo), 1e-12)
    y = np.clip((np.nan_to_num(x, nan=lo) - lo) / span, 0, 1) ** 0.65
    img = Image.fromarray((y * 255).astype(np.uint8), mode="L").convert("RGB")
    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii")


def fits_bytes_to_preview(data: bytes) -> str:
    """Decode a bounded, display-oriented PNG from a FITS image product.

    This is a visual preview only: it does not preserve calibrated units or
    provide a scientifically calibrated difference image.
    """
    if not data:
        raise ValueError("Empty FITS response")

    from astropy.io import fits

    try:
        with fits.open(io.BytesIO(data), memmap=False, lazy_load_hdus=True) as hdul:
            candidates = []
            for index, hdu in enumerate(hdul):
                header = hdu.header
                if int(header.get("NAXIS", 0) or 0) != 2:
                    continue
                nx = int(header.get("NAXIS1", 0) or 0)
                ny = int(header.get("NAXIS2", 0) or 0)
                pixels = nx * ny
                if nx <= 0 or ny <= 0 or pixels > _MAX_FITS_PLANE_PIXELS:
                    continue
                extname = str(header.get("EXTNAME", "PRIMARY" if index == 0 else "")).strip().upper()
                priority = 1 if extname in _SCIENCE_EXTENSIONS else 0
                candidates.append((priority, pixels, index, hdu, nx, ny))

            if not candidates:
                raise ValueError("No safe 2D science image extension was found in the FITS product")

            # Prefer named science/image planes; within that class, use the largest useful plane.
            _, _, _, hdu, nx, ny = max(candidates, key=lambda item: (item[0], item[1]))
            stride = max(1, math.ceil(math.sqrt((nx * ny) / _MAX_PREVIEW_PIXELS)))
            try:
                array = np.asarray(hdu.section[::stride, ::stride])
            except Exception:
                # Some uncommon HDUs do not implement section slicing.
                array = np.asarray(hdu.data)[::stride, ::stride]
            return _png(array)
    except Exception as exc:
        raise ValueError(f"FITS preview decode failed: {exc}") from exc
