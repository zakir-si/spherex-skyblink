from __future__ import annotations

import numpy as np

from backend.science import robust_sigma, detect_moving_candidates


def difference_image(image_a: np.ndarray, image_b: np.ndarray) -> np.ndarray:
    """Return the simple aligned residual B-A."""
    a = np.asarray(image_a, dtype=float)
    b = np.asarray(image_b, dtype=float)
    if a.shape != b.shape:
        raise ValueError("images must have the same shape")
    return b - a


def significance_image(image_a: np.ndarray, image_b: np.ndarray) -> np.ndarray:
    diff = difference_image(image_a, image_b)
    sigma = robust_sigma(diff)
    return np.abs(diff - np.nanmedian(diff)) / sigma


__all__ = ["difference_image", "significance_image", "detect_moving_candidates"]
