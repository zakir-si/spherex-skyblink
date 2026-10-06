import io

import numpy as np
from astropy.io import fits

from backend.fits_preview import fits_bytes_to_preview


def test_fits_preview_decodes_primary_image():
    data = io.BytesIO()
    fits.PrimaryHDU(np.arange(64, dtype=np.float32).reshape(8, 8)).writeto(data)
    preview = fits_bytes_to_preview(data.getvalue())
    assert preview.startswith("data:image/png;base64,")
    assert len(preview) > 100


def test_fits_preview_decodes_largest_2d_extension():
    hdul = fits.HDUList([
        fits.PrimaryHDU(),
        fits.ImageHDU(np.ones((2, 2), dtype=np.float32)),
        fits.ImageHDU(np.ones((8, 8), dtype=np.float32)),
    ])
    data = io.BytesIO()
    hdul.writeto(data)
    preview = fits_bytes_to_preview(data.getvalue())
    assert preview.startswith("data:image/png;base64,")
