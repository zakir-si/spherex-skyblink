from __future__ import annotations


def cutout_from_fits(*args, **kwargs):
    """Placeholder adapter for the production FITS path."""
    try:
        from astropy.io import fits  # noqa: F401
        from astropy.nddata import Cutout2D  # noqa: F401
    except ImportError as exc:
        raise RuntimeError("Install backend/requirements-science.txt for FITS/WCS support.") from exc
    raise NotImplementedError(
        "Implement the SPHEREx-specific MEF cutout adapter here using IRSA cutout URLs."
    )
