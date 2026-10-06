import numpy as np

from backend.science import detect_moving_candidates, robust_sigma


def gaussian(shape, x, y, amp=5, sigma=1.2):
    yy, xx = np.indices(shape)
    return amp * np.exp(-((xx-x)**2+(yy-y)**2)/(2*sigma**2))


def test_robust_sigma_positive():
    x = np.array([0,0,0,1,-1,0,0], dtype=float)
    assert robust_sigma(x) > 0


def test_detector_finds_synthetic_move():
    rng = np.random.default_rng(42)
    a = rng.normal(0,0.05,(64,64))
    b = a.copy()
    a += gaussian(a.shape,20,30,5)
    b += gaussian(b.shape,23,28,5)
    found = detect_moving_candidates(a,b,significance_threshold=4,min_motion_px=.4)
    assert found
    assert found[0].motion_px > .4


def test_detector_rejects_shape_mismatch():
    a = np.zeros((10,10)); b = np.zeros((10,11))
    try:
        detect_moving_candidates(a,b)
    except ValueError as exc:
        assert "same-shape" in str(exc)
    else:
        raise AssertionError("expected ValueError")
