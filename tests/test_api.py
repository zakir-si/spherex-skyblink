from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_demo():
    r = client.get("/api/demo")
    assert r.status_code == 200
    data = r.json()
    assert len(data["frames"]) == 6
    assert len(data["spectrum_wavelength_um"]) == 102
    assert len(data["spectrum_flux_ujy"]) == 102


def test_validation():
    r = client.get("/api/search?ra=999&dec=0&radius_deg=.1")
    assert r.status_code == 422


def test_root_serves_ui():
    r = client.get("/")
    assert r.status_code == 200
    assert "SkyBlink" in r.text
