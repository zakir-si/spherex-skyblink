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
    assert validate_remote_url("https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/x").startswith("https://")
    for url in (
        "https://example.com/x",
        "http://irsa.ipac.caltech.edu/x",
        "https://attacker.amazonaws.com/x",
        "https://user@irsa.ipac.caltech.edu/x",
        "https://irsa.ipac.caltech.edu:8443/x",
        "https://irsa.ipac.caltech.edu/x#fragment",
    ):
        with pytest.raises(ValueError):
            validate_remote_url(url)


def test_cloud_url_does_not_accept_cutout_parameters():
    with pytest.raises(ValueError, match="on-prem"):
        add_cutout_params(
            "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/a.fits",
            83.6, -5.3, 0.1,
        )
