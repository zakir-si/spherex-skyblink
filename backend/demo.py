from __future__ import annotations

import base64
import io
from datetime import datetime, timedelta, timezone

import numpy as np
from PIL import Image

from .models import Candidate, DemoFrame, DemoResponse
from .science import detect_moving_candidates


def _png_data_url(array: np.ndarray) -> str:
    finite = np.nan_to_num(array, nan=0.0)
    lo, hi = np.percentile(finite, [1, 99.7])
    scaled = np.clip((finite - lo) / max(hi - lo, 1e-9), 0, 1) ** 0.65
    rgb = (scaled * 255).astype(np.uint8)
    image = Image.fromarray(rgb, mode="L").convert("RGB")
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def _add_star(frame: np.ndarray, x: float, y: float, amp: float, sigma: float = 1.15) -> None:
    yy, xx = np.indices(frame.shape)
    frame += amp * np.exp(-((xx-x)**2 + (yy-y)**2) / (2*sigma**2))


def build_demo() -> DemoResponse:
    rng = np.random.default_rng(20261006)
    h = w = 256
    frames_raw: list[np.ndarray] = []
    base_time = datetime(2025, 7, 1, tzinfo=timezone.utc)

    stationary = [(54, 78, 3.5), (174, 51, 2.9), (105, 194, 2.3), (201, 178, 2.6), (128, 128, 5.0)]
    moving = (65.0, 150.0)

    for i in range(6):
        frame = rng.normal(0.04, 0.015, size=(h, w)).astype(float)
        for x, y, amp in stationary:
            _add_star(frame, x, y, amp)
        _add_star(frame, moving[0] + i*1.45, moving[1] - i*0.82, 3.1)
        _add_star(frame, 143, 109, 1.5 + 0.45*np.sin(i*1.1))
        frames_raw.append(frame)

    candidates_raw = detect_moving_candidates(frames_raw[0], frames_raw[-1], significance_threshold=4.0, min_motion_px=0.5)
    candidates = [
        Candidate(id=f"SPX-DEMO-{i+1:03d}", x=d.x, y=d.y, dx=d.dx, dy=d.dy,
                  motion_px=d.motion_px, snr=d.snr, score=d.score, kind=d.kind)
        for i, d in enumerate(candidates_raw[:8])
    ]

    frames = [
        DemoFrame(
            id=f"demo-{i+1}",
            timestamp=base_time + timedelta(days=28*i),
            label=f"Demo epoch {i+1}",
            image_data_url=_png_data_url(raw),
            candidate_count=len(candidates),
        )
        for i, raw in enumerate(frames_raw)
    ]

    wavelength = np.linspace(0.75, 5.0, 102)
    flux = 220*np.exp(-0.5*((wavelength-1.55)/0.5)**2) + 75*np.exp(-0.5*((wavelength-3.3)/0.75)**2) + 20
    flux += 4*np.sin(wavelength*8)
    return DemoResponse(
        frames=frames,
        candidates=candidates,
        spectrum_wavelength_um=wavelength.round(5).tolist(),
        spectrum_flux_ujy=flux.round(4).tolist(),
    )
