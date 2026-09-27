# If noise were light

Six article figures, each with the calculated display color as its full background and a wavelength-versus-power graph. Individual PNGs are 2400 × 1500 pixels, tagged sRGB. Matching SVGs retain vector geometry and outlined lettering. `all-six-noise-comparison.png` is an overview; use the individual files in the article for legibility.

| Figure | Background sRGB | Optical model |
| --- | --- | --- |
| Pink | #F5ECFF | Power per optical Hz ∝ 1/f; power per nm ∝ 1/λ |
| White | #D0D7FF | Power per optical Hz is constant; power per nm ∝ 1/λ² |
| Brown / red | #FFE6E2 | Power per optical Hz ∝ 1/f²; power per nm is constant |
| Violet / purple | #94B1FF | Power per optical Hz ∝ f²; power per nm ∝ 1/λ⁴ |
| Grey, by hearing | #FF0052* | A mapped, equal-loudness-weighted audio spectrum |
| Grey, by vision | #7C00FF* | Equal photopic luminance contribution per nm |

*Both grey analogues are outside the sRGB gamut. These hex values are display approximations obtained by clipping a negative linear green channel to zero after common-channel normalization. An ordinary sRGB display cannot reproduce their exact chromaticities. This is labeled in both images; no creative tint or white mixing has been added.

## Common convention

Every figure uses the same 380–700 nm interval and CIE 1931 2° standard observer. Spectral power is integrated against the official 1 nm color-matching functions using the trapezoidal rule. The resulting XYZ values are converted directly to linear sRGB, with no chromatic adaptation. One common scalar sets the largest linear RGB channel to 1; channels outside [0,1] are clipped, then the standard sRGB transfer function and 8-bit rounding are applied.

Each plotted spectrum is independently divided by its own maximum. Thus the graphs compare spectral **shape**, not equal total power. The four power laws have linear power axes; the two grey examples have explicitly labeled logarithmic power axes because their dynamic ranges are large.

The frequency-to-wavelength conversion includes the Jacobian: Sλ = Sf(c/λ) c/λ². Consequently, an optical spectrum described as white noise is not automatically D65 white. The resulting backgrounds are calculations under one shared display convention, not universal colors attached to sound.

## Grey 1: hearing mapped into vision

We use the **60-phon contour from ISO 226:2023**, Equation (1) and Table 1. The 29 sample frequencies span 20–12,500 Hz. The standard specifies pure-tone equal loudness; using its contour as a noise-power weighting is an illustrative model, not a proof of equal loudness across all bands of simultaneous broadband noise.

Let L60(a) be the sound pressure level required for 60 phon at audio frequency a. We interpolate the tabulated dB levels with shape-preserving cubic interpolation (PCHIP) in log audio frequency. The chosen audio power density is:

    Pa(a) ∝ 10^((L60(a) − 60)/10)   [power per audio Hz]

We map log audio frequency affinely onto log optical frequency, with low audio frequencies at the red end:

    a(λ) = 20 × (700/λ)^q
    q = ln(12500/20) / ln(700/380)

This sends 20 Hz to 700 nm and 12.5 kHz to 380 nm. To conserve power in corresponding intervals, the wavelength density is:

    Sλ(λ) = Pa(a(λ)) × |da/dλ|
           = Pa(a(λ)) × q × a(λ)/λ

The audio-to-optical warp and the choice of **per audio Hz**, rather than per octave, matter. A different warp, audio range, loudness level, or bin convention would give a different color. The figure includes the mapped audio-frequency axis so the chosen correspondence is visible.

## Grey 2: compensate human vision directly

We choose equal **photopic luminance contribution per nanometre**, using y-bar, the CIE 1931 photopic response:

    Sλ(λ) ∝ 1 / y-bar(λ)
    Sλ(λ) × y-bar(λ) = constant

Because the eye is most sensitive near 555 nm, this spectrum assigns far less radiant power to the middle green region and far more to the ends. It is not neutral grey: its chromaticity is strongly violet and outside sRGB. “Equal brightness” is operationalized here as equal photopic luminance in equal-width wavelength bins; this is not a complete perceptual brightness model, nor a claim that each cone channel receives equal stimulation.

## Reproduce and verify

From the parent folder, run `python3 generate_noise_figures.py` (NumPy, SciPy, Matplotlib, and Pillow required). The code uses the existing CIE CSV and `data/iso226_2023_parameters.json`. Detailed numerical results are in `color-calculations.json`.

Checks completed:

- The CIE source checksum matches the published dataset, and the four power-law colors match their expected hex values.
- Both mappings reach their stated endpoints; the audio mapping and its inverse agree.
- The ISO calculation returns exactly the specified phon value in dB SPL at 1 kHz.
- Audio and wavelength power integrals agree to better than 7 × 10^-9 relative error on refined grids.
- Refining the two grey integrations from 1 nm to 0.01 nm leaves both 8-bit hex codes unchanged.
- All PNG background pixels match the documented hex codes and contain an sRGB ICC profile.
- Figures were visually inspected, including the axis labels, equations, notes, and gamut labels.

## Sources

- [CIE (2019): Colour-matching functions of CIE 1931 standard colorimetric observer](https://cie.co.at/datatable/cie-1931-colour-matching-functions-2-degree-observer), DOI 10.25039/CIE.DS.xvudnb9b. Original CIE data and these derived figures: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/).
- [International Color Consortium: interpreting sRGB](https://registry.color.org/rgb-registry/files/sRGB.pdf), for the matrix and encoding.
- [MathWorks: dsp.ColoredNoise](https://www.mathworks.com/help/dsp/ref/dsp.colorednoise-system-object.html), for the conventional power laws and the brown/red and violet/purple synonyms.
- [ISO 226:2023](https://www.iso.org/standard/83117.html), Equation (1) and Table 1, for equal-loudness compensation. This is the 2023 formula, not the older 2003 approximation.
- [CIE: the system of physical photometry](https://www.cie.co.at/publications/photometry-cie-system-physical-photometry-2), for the role of the photopic luminous-efficiency function.

To build all figure sets and both color strips, run `python build.py` from the parent folder. See the [project README](../README.md) for setup.
