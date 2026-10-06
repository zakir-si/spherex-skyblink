from __future__ import annotations

import base64
import io

import numpy as np
from PIL import Image


def _png(array: np.ndarray) -> str:
    x = np.asarray(array, dtype=float)
    finite = np.isfinite(x)
    if not finite.any():
        raise ValueError("FITS extension contains no finite pixels")
    lo, hi = np.percentile(x[finite], [1, 99.7])
    y = np.clip((np.nan_to_num(x, nan=lo) - lo) / max(hi - lo, 1e-12), 0, 1) ** 0.65
    img = Image.fromarray((y * 255).astype(np.uint8), mode="L").convert("RGB")
    b = io.BytesIO()
    img.save(b, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(b.getvalue()).decode("ascii")


def fits_bytes_to_preview(data: bytes) -> str:
    try:
        from astropy.io import fits
    except ImportError as exc:
        raise RuntimeError(
            "Astropy is required for live FITS previews. Install backend/requirements-science.txt"
        ) from exc
    with fits.open(io.BytesIO(data), memmap=False, lazy_load_hdus=True) as hdul:
        for hdu in hdul:
            arr = getattr(hdu, "data", None)
            if isinstance(arr, np.ndarray) and arr.ndim == 2 and arr.size:
                return _png(arr)
    raise ValueError("No 2D image extension was found in the FITS product")
