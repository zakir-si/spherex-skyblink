# SPHEREx SkyBlink

SPHEREx SkyBlink is a public-facing explorer for comparing SPHEREx infrared observations over time and turning archive data into an understandable visual timeline.

## Architecture

- Browser: zero-build HTML/CSS/JavaScript viewer.
- API: FastAPI backend for IRSA SIA discovery and secure preview generation.
- Science: Astropy/FITS decoding, NumPy image processing and candidate-ranking pipeline.
- Colab: reproducible astronomy experiments.
- GitHub Actions: automated dependency and test verification.

## Live-data design

SkyBlink uses IRSA SIA v2 for discovery and the SPHEREx-specific cutout mechanism for small spatial subsets. SPHEREx Spectral Image products are multi-extension FITS files, so the browser never attempts to interpret FITS directly.

The live workflow is deliberately bounded:

1. Query IRSA for metadata.
2. Sort observations chronologically.
3. Select at most six preview epochs.
4. Request small cutouts centered on the user's coordinates.
5. Decode FITS with Astropy.
6. Normalize the science plane into a PNG preview.
7. Display the sequence as a timeline, blink and difference view.
8. Keep archive metadata separate from candidate detection.

This prevents a search returning hundreds of observations from accidentally triggering hundreds of FITS downloads.

## Important IRSA constraint

The direct SPHEREx center + size cutout API is intended for on-prem IRSA SPHEREx FITS URLs. SkyBlink therefore rejects unsupported cloud-object URLs for this preview path instead of silently appending parameters that the cloud endpoint does not understand.

## Install

    python -m venv .venv

Windows:

    .venv\\Scripts\\activate

Linux/macOS:

    source .venv/bin/activate

Then:

    pip install -r backend/requirements.txt
    uvicorn backend.main:app --reload

Open http://127.0.0.1:8000.

The normal requirements now include the complete scientific runtime, including Astropy.

## Health check

Open /api/health. A working live environment should report science_ready=true.

## Test

    pytest -q

The tests include FITS decoding, API validation, URL security and synthetic moving-source detection.

## Docker

    docker build -t spherex-skyblink .
    docker run --rm -p 8000:8000 spherex-skyblink

Docker installs the scientific runtime automatically.

## Science caution

SkyBlink produces candidate signals, not discoveries. A difference can come from a genuine moving or variable source, imperfect WCS registration, detector/systematic effects, cosmic rays, or background changes. Scientific claims require validation against calibrated data products, uncertainty information and independent catalogs.

## Roadmap

- WCS-aware registration across epochs.
- Science/variance/mask-aware difference imaging.
- SPHEREx spectrophotometry extraction.
- Known-object crossmatching.
- Human-labeled candidate review.
- Reproducible candidate exports with data-release provenance.
