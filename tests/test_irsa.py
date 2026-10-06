from backend.irsa import parse_sia_csv


def test_parse_sia_csv():
    csv = """obs_id,obs_collection,s_ra,s_dec,t_min,t_max,em_min,em_max,access_url,access_format,access_estsize
abc123,spherex_qr3,83.63,-5.39,60800.1,60800.2,7.5e-7,5e-6,https://example.test/a.fits,image/fits,12345
"""
    rows = parse_sia_csv(csv, "spherex_qr3")
    assert len(rows) == 1
    row = rows[0]
    assert row.obs_id == "abc123"
    assert row.ra == 83.63
    assert row.wavelength_min_m == 7.5e-7
    assert row.estimated_size_kb == 12345
