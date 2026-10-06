from backend import irsa


class FakeResponse:
    status_code = 200
    text = "obs_id,s_ra,s_dec\nabc,83.6,-5.3\n"

    def raise_for_status(self):
        pass


def test_query_contract(monkeypatch):
    seen = {}

    def fake_get(url, params, timeout):
        seen.update(params)
        return FakeResponse()

    monkeypatch.setattr(irsa.requests, "get", fake_get)
    rows = irsa.search_spherex(83.6, -5.3, 0.1, 2.2)
    assert rows[0].obs_id == "abc"
    assert seen["POS"] == "CIRCLE 83.6 -5.3 0.1"
    assert seen["DPTYPE"] == "image"
    assert seen["CALIB"] == "2"
    assert seen["FORMAT"] == "image/fits"
    assert seen["BAND"] == "2.2e-06"
