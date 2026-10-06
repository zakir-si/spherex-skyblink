# SPHEREx SkyBlink

A public-facing explorer for comparing SPHEREx infrared sky observations over time.

SkyBlink is deliberately built as a small, reproducible stack:

- **Browser:** zero-build HTML/CSS/JavaScript viewer.
- **API:** FastAPI backend for IRSA SIA search and image/cutout operations.
- **Science pipeline:** Python/NumPy statistical image differencing, with optional Astropy/FITS support.
- **Colab:** notebooks for data access, alignment, difference imaging and candidate ranking.
- **GitHub:** source control, tests, documentation and CI.

## Current data assumptions

SPHEREx Quick Release data are provided by IRSA. SkyBlink uses the IRSA SIA v2 interface for discovery and the SPHEREx cutout service for small spatial subsets. The default collection is configurable through `SPHEREX_COLLECTION` and currently defaults to `spherex_qr3`.

> **Science note:** SkyBlink reports *candidates*, not discoveries. A detected residual can be caused by a real moving/variable source, imperfect registration, detector effects, artifacts, or other systematics.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

Open http://127.0.0.1:8000

The **Demo sky** works without Astropy or live archive access, so the UI can be developed and tested offline.

## Live SPHEREx mode

Install the full scientific dependencies:

```bash
pip install -r backend/requirements-science.txt
```

Then use the SkyBlink search form. The backend queries IRSA SIA v2 and returns observation metadata. A production deployment should add caching and rate limiting rather than forwarding every browser request directly to IRSA.

## Test

```bash
pytest -q
```

The test suite covers validation, candidate detection, demo generation and API health. A live IRSA test is intentionally optional because archive availability/network access varies by environment.

## Project status

### MVP implemented

- polished web UI
- coordinate input + radius controls
- demo six-epoch sky sequence
- blink playback
- previous/next timeline controls
- difference image view
- basic statistical candidate detection
- candidate list + object inspector
- spectrum panel with 102 synthetic/demo channels to exercise the UI
- IRSA SIA v2 search endpoint
- remote FITS preview path with URL allowlisting
- science-ready pipeline modules
- Colab notebook
- GitHub Actions test workflow

### Next science milestones

1. Run the live IRSA SIA search against QR3.
2. Add a robust FITS/WCS cutout endpoint using Astropy + the SPHEREx cutout service.
3. Replace demo spectra with extracted SPHEREx photometry/spectrophotometry.
4. Cross-match candidate positions with known-object catalogs and MOST.
5. Build a human-labeled candidate set before training ML.

## Attribution

When using SPHEREx QR data in published work, follow IRSA's release-specific DOI and acknowledgement requirements. SkyBlink should preserve the source release and data DOI in exported metadata.

## Deploy with Docker

```bash
docker build -t spherex-skyblink .
docker run --rm -p 8000:8000 spherex-skyblink
```
