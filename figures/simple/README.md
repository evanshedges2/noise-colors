# Simplified noise figures

Each image contains a short title, the calculated-color background, the power spectrum, and labeled axes. The titles are “Pink Noise”, “White Noise”, “Brown Noise”, “Violet Noise”, “Grey Noise (Hearing)”, and “Grey Noise (Vision)”. Formulas, hex codes, explanatory text, and credits are omitted from the visible artwork. Detailed figures and the text-free teaser are in the parent folder.

The individual PNGs are 2400 × 1500 pixels with an embedded sRGB profile. Matching SVGs are also included. Image metadata retains the title, assumptions, and attribution without displaying them. The overview is ordered pink / white, brown / violet, then grey by hearing / grey by vision.

## Information to retain in the post

Shared caption: “Optical display approximations over 380–700 nm, calculated using the CIE 1931 2° observer and direct sRGB/D65 conversion. Each curve is independently normalized to its peak; display brightness is normalized so the brightest linear RGB channel equals 1.”

The two grey examples use logarithmic power axes, marked on the axes. Both grey backgrounds are clipped sRGB approximations of out-of-gamut colors. The hearing example uses the ISO 226:2023 60-phon curve as a per-audio-Hz power weighting, mapped logarithmically from 20–12,500 Hz into 700–380 nm with the power-preserving Jacobian. The vision example uses Sλ ∝ 1/y-bar(λ), giving equal photopic luminance contribution per nanometre.

Data attribution for the post: CIE (2019), *Colour-matching functions of CIE 1931 standard colorimetric observer*, DOI [10.25039/CIE.DS.xvudnb9b](https://doi.org/10.25039/CIE.DS.xvudnb9b), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). These derived figures use the same license. The hearing model also uses [ISO 226:2023](https://www.iso.org/standard/83117.html).

The full derivations and sources are in [the figure notes](../README.md) and [methods](../../methods.md). Run `python3 generate_simple_noise_figures.py` from the project folder to regenerate only these simplified companions.
