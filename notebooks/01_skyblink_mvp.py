# This file is intentionally valid Python so it can be opened as a Colab notebook source.
# In Google Colab, upload/copy it or convert with Jupytext if desired.

# %% [markdown]
# # SPHEREx SkyBlink — MVP science notebook
# This notebook demonstrates the scientific core on synthetic data, then sketches the IRSA SIA v2 path.

# %%
!pip -q install numpy pandas matplotlib scipy astropy astroquery pyvo requests pillow

# %%
import numpy as np
import matplotlib.pyplot as plt
from backend.science import detect_moving_candidates

# %% [markdown]
# ## 1. Build a toy two-epoch field

# %%
def gaussian(shape, x, y, amp=4, sigma=1.2):
    yy, xx = np.indices(shape)
    return amp*np.exp(-((xx-x)**2 + (yy-y)**2)/(2*sigma**2))

rng = np.random.default_rng(123)
a = rng.normal(0, 0.04, (128,128))
b = rng.normal(0, 0.04, (128,128))
for x,y in [(30,30),(90,72),(48,106)]:
    a += gaussian(a.shape,x,y,4)
    b += gaussian(b.shape,x,y,4)
a += gaussian(a.shape,60,80,5)
b += gaussian(b.shape,65,76,5)

# %%
plt.figure(figsize=(6,6)); plt.imshow(a, origin="lower", cmap="magma"); plt.title("Epoch A"); plt.show()
plt.figure(figsize=(6,6)); plt.imshow(b, origin="lower", cmap="magma"); plt.title("Epoch B"); plt.show()

# %% [markdown]
# ## 2. Detect significant motion

# %%
candidates = detect_moving_candidates(a, b, significance_threshold=4, min_motion_px=.5)
for c in candidates[:10]:
    print(c)

# %% [markdown]
# ## 3. Live IRSA discovery
# IRSA exposes SIA v2 for image discovery. Use the current collection in SPHEREX_COLLECTION.

# %%
from pyvo.dal import sia2
from astropy.coordinates import SkyCoord
import astropy.units as u

service = sia2.SIAService("https://irsa.ipac.caltech.edu/SIA")
collection = "spherex_qr3"
pos = SkyCoord(ra=83.633*u.deg, dec=-5.391*u.deg, frame="icrs")

# results = service.search(pos=(pos.ra.deg, pos.dec.deg, 0.1*u.deg), collection=collection)
# table = results.to_table()
# table

# %% [markdown]
# ## 4. Production next step
# Filter access_url values, request small SPHEREx cutouts, read the MEF with Astropy, use each extension's WCS, align common bands, then feed aligned pairs into detect_moving_candidates.
