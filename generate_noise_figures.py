"""Reproducible, colorimetric article figures; no AI-generated chart geometry.

Run: python3 generate_noise_figures.py
Creates four power-law figures and two explicitly defined grey-noise analogues.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "noise-colors-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager, ticker
import numpy as np
from PIL import Image, ImageCms
from scipy.interpolate import PchipInterpolator
from scipy.integrate import trapezoid

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figures"
OUT.mkdir(exist_ok=True)
DATA = ROOT / "data" / "CIE_xyz_1931_2deg.csv"
assert hashlib.md5(DATA.read_bytes()).hexdigest() == "17cca777db64b17170f06f67ce9d3ab7"
CIE = np.loadtxt(DATA, delimiter=",")
CIE = CIE[(CIE[:, 0] >= 380) & (CIE[:, 0] <= 700)]
WAVELENGTHS = CIE[:, 0]
CMF = CIE[:, 1:]
XYZ_TO_RGB = np.array([
    [3.2406255, -1.537208, -.4986286],
    [-.9689307, 1.8757561, .0415175],
    [.0557101, -.2040211, 1.0569959],
])
ICC = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
try:
    SERIF = font_manager.FontProperties(fname=font_manager.findfont("Georgia", fallback_to_default=False))
except ValueError:
    SERIF = font_manager.FontProperties(family="DejaVu Serif")
SANS = font_manager.FontProperties(family="DejaVu Sans")
ISO226 = json.loads((ROOT / "data" / "iso226_2023_parameters.json").read_text(encoding="utf-8"))
AUDIO_MIN, AUDIO_MAX, PHON = 20., 12500., 60.
MAPPING_Q = np.log(AUDIO_MAX / AUDIO_MIN) / np.log(700 / 380)

plt.rcParams.update({
    "font.family": "DejaVu Sans", "mathtext.fontset": "stix",
    "svg.fonttype": "path", "axes.unicode_minus": False,
    "savefig.transparent": False,
})

SPECS = [
    dict(slug="pink", name="Pink noise", alpha=1,
         definition="Equal power per octave.",
         frequency=r"S_f\,\propto\,1/f", wavelength=r"S_\lambda\,\propto\,1/\lambda",
         insight="A hint of pink.\nA little lavender.",
         note="A display approximation of a 1/f light spectrum.",
         expected="#F5ECFF"),
    dict(slug="white", name="White noise", alpha=0,
         definition="Equal power per hertz.",
         frequency=r"S_f\,=\,\mathrm{constant}", wavelength=r"S_\lambda\,\propto\,1/\lambda^2",
         insight="White by name.\nBluish on this display.",
         note="Flat per hertz is not flat per nanometre, or D65 white.",
         expected="#D0D7FF"),
    dict(slug="brown", name="Brown Noise", alpha=2,
         definition="Brownian noise. Also called red noise.",
         frequency=r"S_f\,\propto\,1/f^2", wavelength=r"S_\lambda\,=\,\mathrm{constant}",
         insight="More red than pink.\nStill a very pale tint.",
         note="The 1/f² law becomes equal power per nanometre.",
         expected="#FFE6E2"),
    dict(slug="violet", name="Violet Noise", alpha=-2,
         definition="Also called purple noise.",
         frequency=r"S_f\,\propto\,f^2", wavelength=r"S_\lambda\,\propto\,1/\lambda^4",
         insight="A name is not\na paint sample.",
         note="This convention gives a periwinkle-blue display color.",
         expected="#94B1FF"),
]


def iso226_spl(phon=60):
    """ISO 226:2023 Eq. (1), evaluated at the 29 tabulated frequencies."""
    alpha = np.array(ISO226["alpha_f"])
    lu = np.array(ISO226["L_U_db"])
    threshold = np.array(ISO226["T_f_db"])
    pressure = ((4e-10) ** (.3 - alpha) * (10 ** (.03 * phon) - 10 ** .072)
                + 10 ** (alpha * (threshold + lu) / 10))
    spl = 10 / alpha * np.log10(pressure) - lu
    assert abs(spl[17] - phon) < 1e-10
    return spl


def audio_at_wavelength(wavelength):
    return AUDIO_MIN * (700 / np.asarray(wavelength)) ** MAPPING_Q


def wavelength_at_audio(frequency):
    return 700 * (np.maximum(np.asarray(frequency), 1e-12) / AUDIO_MIN) ** (-1 / MAPPING_Q)


def hearing_spectrum(wavelengths, phon=PHON):
    # Pure-tone contour used as a per-Hz noise-power proxy, not a full loudness model.
    audio = np.clip(audio_at_wavelength(wavelengths), AUDIO_MIN, AUDIO_MAX)
    interpolator = PchipInterpolator(np.log(ISO226["frequency_hz"]), iso226_spl(phon))
    spl = interpolator(np.log(audio))
    per_hz = 10 ** ((spl - phon) / 10)
    jacobian = MAPPING_Q * audio / wavelengths  # |d(audio Hz)/d(wavelength nm)|
    return per_hz * jacobian


def calculate(spectrum):
    xyz = trapezoid(spectrum[:, None] * CMF, WAVELENGTHS, axis=0)
    linear = XYZ_TO_RGB @ xyz
    linear /= max(linear)
    clipped = np.clip(linear, 0, 1)
    encoded = np.where(clipped <= .0031308, 12.92 * clipped,
                       1.055 * clipped ** (1 / 2.4) - .055)
    rgb = np.rint(encoded * 255).astype(int)
    return dict(
        xyz=xyz.tolist(), xy=(xyz[:2] / sum(xyz)).tolist(),
        linear_rgb=linear.tolist(),
        clipped_channels=[n for n, v in zip("RGB", linear) if v < -1e-8 or v > 1 + 1e-8],
        rgb=rgb.tolist(), hex="#" + "".join(f"{n:02X}" for n in rgb),
    )


def text(fig, x, y, value, size=17, color="#282432", serif=False, **kwargs):
    return fig.text(x, y, value, fontsize=size, color=color,
                    fontproperties=SERIF if serif else SANS, **kwargs)


def make_figure(spec):
    is_vision = spec["slug"] == "grey-vision"
    is_hearing = spec["slug"] == "grey-hearing"
    is_grey = is_vision or is_hearing
    if is_vision:
        # Equal photopic luminance contribution in each equal-width wavelength bin.
        # Deliberately NOT presented as a canonical optical spectrum of grey noise.
        spectrum = 1 / CMF[:, 1]
        assert np.allclose(spectrum * CMF[:, 1], 1)
    elif is_hearing:
        spectrum = hearing_spectrum(WAVELENGTHS)
    else:
        spectrum = (WAVELENGTHS / 550) ** (spec["alpha"] - 2)
    result = calculate(spectrum)
    if "expected" in spec:
        assert result["hex"] == spec["expected"]
    normalized = spectrum / max(spectrum)
    background = result["hex"]
    dark_background = is_vision
    ink = "#FFFFFF" if dark_background else "#282432"
    subtle = "#EFDEFF" if dark_background else "#514956"
    line = "#FFFFFF" if dark_background else "#393040"
    if is_hearing:
        ink = subtle = line = "#17101C"
    fig = plt.figure(figsize=(16, 10), dpi=150, facecolor=background)
    texts = []
    texts.append(text(fig, .055, .914, "IF NOISE WERE LIGHT", 13, subtle, weight="medium"))
    texts.append(text(fig, .945, .914, "380–700 nm", 13, subtle, ha="right"))
    texts.append(text(fig, .055, .785, spec["name"], 41 if is_grey else 46, ink, serif=True))
    texts.append(text(fig, .057, .731, spec["definition"], 17, subtle))

    if is_vision:
        texts.append(text(fig, .057, .626, "VISION-BASED ANALOGUE", 12, subtle))
        texts.append(text(fig, .055, .562, "$S_\\lambda\\,\\overline{y}(\\lambda)=\\mathrm{constant}$", 26, ink))
        texts.append(text(fig, .057, .475, "Equal photopic contribution\nper nanometre.", 17, ink, linespacing=1.5))
    elif is_hearing:
        texts.append(text(fig, .057, .626, "HEARING-BASED ANALOGUE", 12, subtle))
        texts.append(text(fig, .055, .562, "60 phon", 31, ink, serif=True))
        texts.append(text(fig, .057, .475, "ISO 226:2023\nEqual-loudness compensation", 16, ink, linespacing=1.5))
    else:
        texts.append(text(fig, .057, .626, "POWER PER UNIT FREQUENCY", 12, subtle))
        texts.append(text(fig, .055, .560, "$" + spec["frequency"] + "$", 31, ink))
    texts.append(text(fig, .057, .377, spec["insight"], 24, ink, serif=True, linespacing=1.35))
    texts.append(text(fig, .057, .220, background, 19, ink))
    texts.append(text(fig, .057, .185, "sRGB approximation · green clipped" if result["clipped_channels"] else "Calculated sRGB", 12, subtle))

    ax = fig.add_axes([.460, .252, .479, .420 if is_hearing else .482], facecolor=background)
    ax.set_xlim(380, 700)
    low = 10. ** np.floor(np.log10(min(normalized)))
    ax.set_ylim((low, 1.4) if is_grey else (0, 1.08))
    if is_grey:
        ax.set_yscale("log")
        ticks = 10. ** np.arange(round(np.log10(low)), 1)
        ax.set_yticks(ticks)
        ax.set_yticklabels([f"{v:g}" for v in ticks])
        ax.minorticks_off()
    else:
        ax.set_yticks([0, .25, .50, .75, 1])
        ax.set_yticklabels(["0", "0.25", "0.50", "0.75", "1.00"])
    ax.set_xticks([400, 450, 500, 550, 600, 650, 700])
    ax.tick_params(axis="both", which="both", labelsize=13, colors=subtle, length=0, pad=10)
    for spine in ["top", "right"]:
        ax.spines[spine].set_visible(False)
    for spine in ["left", "bottom"]:
        ax.spines[spine].set_color(ink)
        ax.spines[spine].set_alpha(.38)
        ax.spines[spine].set_linewidth(.8)
    ax.grid(axis="y", color=ink, alpha=.13, linewidth=.7)
    ax.set_axisbelow(True)
    ax.plot(WAVELENGTHS, normalized, color=line, linewidth=3.1, solid_capstyle="round")
    ax.set_xlabel("Wavelength (nm)", fontsize=16, color=ink, labelpad=17, fontproperties=SANS)
    ax.set_ylabel("Relative power per nm" + (" · log scale" if is_grey else ""),
                  fontsize=15, color=ink, labelpad=15, fontproperties=SANS)
    if is_hearing:
        top = ax.secondary_xaxis('top', functions=(audio_at_wavelength, wavelength_at_audio))
        top.set_xticks([12500, 1000, 100, 20])
        top.set_xticklabels(["12.5k", "1k", "100", "20"])
        top.tick_params(labelsize=12, colors=subtle, length=0, pad=8)
        top.set_xlabel("Mapped audio frequency (Hz)", fontsize=12, color=ink, labelpad=10)
        top.spines['top'].set_visible(False)
        texts.append(text(fig, .700, .835, "$" + spec["wavelength"] + "$", 25, ink, ha="center"))
        texts.append(text(fig, .700, .796, "Power-conserving log-frequency mapping · peak = 1", 11, subtle, ha="center"))
    else:
        texts.append(text(fig, .700, .808, "$" + spec["wavelength"] + "$", 30, ink, ha="center"))
        texts.append(text(fig, .700, .759, "Spectral density · maximum = 1", 11, subtle, ha="center"))

    fig.add_artist(plt.Line2D([.055, .945], [.128, .128], color=ink, alpha=.23, linewidth=.7))
    texts.append(text(fig, .055, .091, spec["note"], 13, ink))
    texts.append(text(fig, .055, .057,
                      "CIE 1931 2° · sRGB / D65 · peak linear RGB = 1 · no white-balance adjustment",
                      10.5, subtle))
    texts.append(text(fig, .055, .027,
                      "CIE (2019): doi:10.25039/CIE.DS.xvudnb9b · CC BY-SA 4.0" + (" · Hearing model: ISO 226:2023, 60 phon" if is_hearing else " · data & derived figure"),
                      9, subtle))
    # Confirm every text item stays inside the intended image boundary.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for artist in texts + ax.get_xticklabels() + ax.get_yticklabels() + [ax.xaxis.label, ax.yaxis.label]:
        box = artist.get_window_extent(renderer)
        assert box.x0 >= 0 and box.y0 >= 0 and box.x1 <= 2400 and box.y1 <= 1500, (spec["slug"], artist.get_text(), box)

    stem = OUT / (spec["slug"] + "-noise")
    fig.savefig(stem.with_suffix(".png"), dpi=150, facecolor=background)
    fig.savefig(stem.with_suffix(".svg"), facecolor=background,
                metadata={"Title": spec["name"], "Description": spec["note"],
                          "Creator": "Matplotlib; CIE 1931 observer integration",
                          "Rights": "CIE data and derived figure: CC BY-SA 4.0"})
    plt.close(fig)
    # An explicit sRGB profile prevents an untagged image from being interpreted
    # in another RGB color space by a publication or image editor.
    with Image.open(stem.with_suffix(".png")) as im:
        im = im.convert("RGB")
        assert im.size == (2400, 1500)
        assert im.getpixel((0, 0)) == tuple(result["rgb"])
        im.save(stem.with_suffix(".png"), icc_profile=ICC, dpi=(150, 150))
    return {
        **spec, **result, "wavelength_interval_nm": [380, 700],
        "graph": "power per unit wavelength, independently peak-normalized",
        "background": "direct CIE XYZ to sRGB; max linear channel = 1; clip then encode",
        "optical_analogue_only": is_grey,
        "audio_mapping": ({"phon": PHON, "audio_range_hz": [AUDIO_MIN, AUDIO_MAX], "map": "audio = 20*(700/lambda_nm)^q", "q": float(MAPPING_Q), "jacobian": "q*audio/lambda_nm", "interpolation": "PCHIP of dB SPL in log audio Hz", "power_convention": "per Hz before mapping"} if is_hearing else None),
        "spectrum_peak_normalized_endpoints": [float(normalized[0]), float(normalized[-1])],
    }


def main():
    specs = list(SPECS)
    specs.extend([
        dict(
            slug="grey-hearing", name="Grey, by hearing", alpha=None,
            definition="Audio frequencies mapped into light.",
            wavelength=r"S_\lambda\,=\,P_a(a(\lambda))\,|da/d\lambda|",
            insight="Compensate the ear.\nThen translate to light.",
            note="20 Hz → 700 nm; 12.5 kHz → 380 nm. A chosen audio-to-light mapping; color outside sRGB.",
        ),
        dict(
            slug="grey-vision", name="Grey, by vision", alpha=None,
            definition="Equal luminance from each wavelength.",
            wavelength=r"S_\lambda\,\propto\,1/\overline{y}(\lambda)",
            insight="Less green power.\nFar from grey.",
            note="An optical analogue, not standard audio grey noise. The true color is outside sRGB.",
        ),
    ])
    manifest = [make_figure(spec) for spec in specs]
    (OUT / "color-calculations.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    # A compact overview for reviewing the four ordinary power-law cases.
    sheet = Image.new("RGB", (2400, 1500))
    for spec, location in zip(SPECS, [(0, 0), (1200, 0), (0, 750), (1200, 750)]):
        with Image.open(OUT / (spec["slug"] + "-noise.png")) as im:
            sheet.paste(im.resize((1200, 750), Image.Resampling.LANCZOS), location)
    sheet.save(OUT / "four-noise-comparison.png", icc_profile=ICC)
    all_sheet = Image.new("RGB", (2400, 2250))
    for i, spec in enumerate(specs):
        with Image.open(OUT / (spec["slug"] + "-noise.png")) as im:
            all_sheet.paste(im.resize((1200, 750), Image.Resampling.LANCZOS), ((i % 2) * 1200, (i // 2) * 750))
    all_sheet.save(OUT / "all-six-noise-comparison.png", icc_profile=ICC)
    print(json.dumps([{k: row[k] for k in ["name", "hex", "xy", "clipped_channels"]} for row in manifest], indent=2))


if __name__ == "__main__":
    main()
