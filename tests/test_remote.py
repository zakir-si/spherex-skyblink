import pytest

from backend.remote import add_cutout_params, validate_remote_url


def test_cutout_url():
    u = add_cutout_params(
        "https://irsa.ipac.caltech.edu/ibe/data/spherex/a.fits", 83.6, -5.3, 0.1
    )
    assert "center=83.60000000%2C-5.30000000" in u
    assert "size=0.100000" in u


def test_allowlist():
    assert validate_remote_url("https://irsa.ipac.caltech.edu/x").startswith("https://")
    with pytest.raises(ValueError):
        validate_remote_url("https://example.com/x")
    with pytest.raises(ValueError):
        validate_remote_url("http://irsa.ipac.caltech.edu/x")
