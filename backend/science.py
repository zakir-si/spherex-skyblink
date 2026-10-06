from __future__ import annotations

from dataclasses import dataclass
import math

import numpy as np


@dataclass(frozen=True)
class Detection:
    y: int
    x: int
    dx: float
    dy: float
    motion_px: float
    snr: float
    score: float
    kind: str


def robust_sigma(values: np.ndarray) -> float:
    """Median absolute deviation based noise estimate."""
    finite = values[np.isfinite(values)]
    if finite.size == 0:
        return 1.0
    med = np.median(finite)
    mad = np.median(np.abs(finite - med))
    sigma = 1.4826 * mad
    return float(max(sigma, np.finfo(float).eps))


def local_centroid(image: np.ndarray, y: int, x: int, half_width: int = 2) -> tuple[float, float]:
    y0, y1 = max(0, y-half_width), min(image.shape[0], y+half_width+1)
    x0, x1 = max(0, x-half_width), min(image.shape[1], x+half_width+1)
    patch = np.asarray(image[y0:y1, x0:x1], dtype=float)
    patch = np.nan_to_num(patch, nan=0.0)
    baseline = np.percentile(patch, 25)
    weights = np.clip(patch - baseline, 0, None)
    total = weights.sum()
    if total <= 0:
        return float(x), float(y)
    yy, xx = np.indices(weights.shape)
    return float((xx * weights).sum() / total + x0), float((yy * weights).sum() / total + y0)


def detect_moving_candidates(
    image_a: np.ndarray,
    image_b: np.ndarray,
    *,
    significance_threshold: float = 5.0,
    min_motion_px: float = 0.75,
    max_candidates: int = 50,
) -> list[Detection]:
    """Detect significant residuals and pair them by local centroid displacement.

    This is an intentionally conservative MVP detector. It expects already aligned images.
    It is not a survey-grade transient pipeline and must be calibrated against flags/PSF/systematics.
    """
    a = np.asarray(image_a, dtype=float)
    b = np.asarray(image_b, dtype=float)
    if a.shape != b.shape or a.ndim != 2:
        raise ValueError("image_a and image_b must be same-shape 2D arrays")

    diff = b - a
    sigma = robust_sigma(diff)
    z = np.abs(diff - np.nanmedian(diff)) / sigma

    flat_idx = np.argwhere(z >= significance_threshold)
    if flat_idx.size == 0:
        return []

    strengths = np.array([z[y, x] for y, x in flat_idx])
    order = np.argsort(strengths)[::-1]
    detections: list[Detection] = []
    used: list[tuple[int, int]] = []

    for idx in order:
        y, x = map(int, flat_idx[idx])
        if any((x-ux)**2 + (y-uy)**2 <= 25 for uy, ux in used):
            continue

        xa, ya = local_centroid(a, y, x)
        xb, yb = local_centroid(b, y, x)
        dx, dy = xb - xa, yb - ya
        motion = math.hypot(dx, dy)
        snr = float(z[y, x])
        if motion < min_motion_px:
            continue

        score = float(min(1.0, 0.55 * snr / 10.0 + 0.45 * min(motion / 4.0, 1.0)))
        detections.append(Detection(y, x, dx, dy, motion, snr, score, "moving-source"))
        used.append((x, y))
        if len(detections) >= max_candidates:
            break

    detections.sort(key=lambda d: d.score, reverse=True)
    return detections
