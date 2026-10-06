# Science design

## Candidate equation

For two already aligned images, the first-order residual is

`D(x,y) = I_2(x,y) - I_1(x,y)`

We estimate a robust noise scale using the median absolute deviation:

`sigma ~= 1.4826 * MAD(D)`

Then rank high-significance pixels and estimate source centroids in small local windows.

## Limitations

The MVP detector does **not** yet model the SPHEREx PSF, detector flags, WCS uncertainty, correlated noise, zodiacal background, or inter-band timing. It must not be interpreted as a scientific discovery pipeline.

## Production science work

- use the MEF's per-extension WCS
- propagate quality/status flags
- compare like-for-like detector/band products
- PSF-aware subtraction
- robust background modelling
- sub-pixel registration
- object clustering / track linking across epochs
- cross-match against known solar-system objects
- human review before public candidate labels
