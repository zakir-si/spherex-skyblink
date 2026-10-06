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
    if not np.isfinite(lo) or not np.isfinite(hi):
        raise ValueError("FITS extension has invalid percentile statistics")

    span = max(float(hi - lo), 1e-12)
    y = np.clip((np.nan_to_num(x, nan=lo) - lo) / span, 0, 1) ** 0.65
    img = Image.fromarray((y * 255).astype(np.uint8), mode="L").convert("RGB")

    out = io.BytesIO()
    img.save(out, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(out.getvalue()).decode("ascii")


def fits_bytes_to_preview(data: bytes) -> str:
    if not data:
        raise ValueError("Empty FITS response")

    from astropy.io import fits

    try:
        with fits.open(io.BytesIO(data), memmap=False, lazy_load_hdus=True) as hdul:
            # Prefer the primary/science-like 2-D image, but tolerate MEF products.
            candidates = []
            for index, hdu in enumerate(hdul):
                arr = getattr(hdu, "data", None)
                if isinstance(arr, np.ndarray) and arr.ndim == 2 and arr.size:
                    candidates.append((index, arr))

            if not candidates:
                raise ValueError("No 2D image extension was found in the FITS product")

            # Prefer the largest 2-D plane; SPHEREx MEFs can contain several 2-D HDUs.
            _, array = max(candidates, key=lambda item: item[1].size)
            return _png(array)
    except Exception as exc:
        raise ValueError(f"FITS preview decode failed: {exc}") from exc
