"""Create simply labeled plot companions without rewriting any detailed figure.

Run: python3 generate_simple_noise_figures.py
Uses exactly the spectra and display colors of the detailed figure set.
"""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode = True
import generate_noise_figures as model
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image, PngImagePlugin

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figures" / "simple"
OUT.mkdir(exist_ok=True)
MANIFEST = json.loads((ROOT / "figures" / "color-calculations.json").read_text(encoding="utf-8"))
LABELS = {
    "pink": "Pink Noise",
    "white": "White Noise",
    "brown": "Brown Noise",
    "violet": "Violet Noise",
    "grey-vision": "Grey Noise (Vision)",
    "grey-hearing": "Grey Noise (Hearing)",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_simple(spec):
    slug = spec["slug"]
    grey = slug.startswith("grey-")
    if slug == "grey-vision":
        spectrum = 1 / model.CMF[:, 1]
    elif slug == "grey-hearing":
        spectrum = model.hearing_spectrum(model.WAVELENGTHS)
    else:
        spectrum = (model.WAVELENGTHS / 550) ** (spec["alpha"] - 2)
    calculated = model.calculate(spectrum)
    assert calculated["hex"] == spec["hex"]
    y = spectrum / spectrum.max()
    background = spec["hex"]
    ink = "#FFFFFF" if slug == "grey-vision" else "#17101C" if slug == "grey-hearing" else "#302937"
    fig = plt.figure(figsize=(16, 10), dpi=150, facecolor=background)
    ax = fig.add_axes([.155, .170, .780, .745], facecolor=background)
    ax.set_title(LABELS[slug], fontsize=30, fontweight="normal", color=ink, pad=20)
    ax.set_xlim(380, 700)
    ax.set_xticks([400, 450, 500, 550, 600, 650, 700])
    if grey:
        low = 10. ** np.floor(np.log10(y.min()))
        ax.set_yscale("log")
        ax.set_ylim(low, 1.45)
        exponents = np.arange(round(np.log10(low)), 1)
        ax.set_yticks(10. ** exponents)
        ax.set_yticklabels(["1" if exponent == 0 else rf"$10^{{{exponent}}}$" for exponent in exponents])
        ax.minorticks_off()
    else:
        ax.set_ylim(0, 1.08)
        ax.set_yticks([0, .25, .5, .75, 1])
        ax.set_yticklabels(["0", "0.25", "0.50", "0.75", "1.00"])
    ax.tick_params(axis="both", labelsize=19, colors=ink, length=0, pad=14)
    for edge in ["top", "right"]:
        ax.spines[edge].set_visible(False)
    for edge in ["left", "bottom"]:
        ax.spines[edge].set_color(ink)
        ax.spines[edge].set_alpha(.40)
        ax.spines[edge].set_linewidth(1)
    ax.grid(axis="y", color=ink, alpha=.12, linewidth=.8)
    ax.set_axisbelow(True)
    ax.plot(model.WAVELENGTHS, y, color=ink, linewidth=3.3, solid_capstyle="round")
    ax.set_xlabel("Wavelength (nm)", fontsize=23, color=ink, labelpad=22)
    ax.set_ylabel("Relative power per nm" + (" (log scale)" if grey else ""),
                  fontsize=23, color=ink, labelpad=24)
    assert not fig.texts and len(ax.lines) == 1 and ax.get_title() == LABELS[slug]
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for artist in ax.get_xticklabels() + ax.get_yticklabels() + [ax.xaxis.label, ax.yaxis.label, ax.title]:
        bounds = artist.get_window_extent(renderer)
        assert 0 <= bounds.x0 < bounds.x1 <= 2400
        assert 0 <= bounds.y0 < bounds.y1 <= 1500

    stem = OUT / f"{slug}-noise-simple"
    description = (f"{spec['name']}. {spec['note']} 380–700 nm; curve normalized to its peak. "
                   "CIE 1931 2 degree observer; direct sRGB/D65 conversion; peak linear RGB=1. "
                   f"Background {background}; clipped channels: {', '.join(calculated['clipped_channels']) or 'none'}.")
    credit = "CIE (2019), doi:10.25039/CIE.DS.xvudnb9b. CIE data and derived figure: CC BY-SA 4.0."
    fig.savefig(stem.with_suffix(".png"), dpi=150, facecolor=background)
    fig.savefig(stem.with_suffix(".svg"), facecolor=background, metadata={
        "Title": LABELS[slug], "Description": description,
        "Creator": "Matplotlib; CIE 1931 observer integration", "Rights": credit,
    })
    plt.close(fig)
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Title", LABELS[slug])
    metadata.add_text("Description", description)
    metadata.add_text("Copyright", credit)
    with Image.open(stem.with_suffix(".png")) as source:
        image = source.convert("RGB")
        assert image.size == (2400, 1500)
        assert image.getpixel((0, 0)) == tuple(spec["rgb"])
        image.save(stem.with_suffix(".png"), icc_profile=model.ICC, pnginfo=metadata, dpi=(150, 150))


def main():
    originals = {path: digest(path) for path in (ROOT / "figures").iterdir() if path.is_file()}
    for spec in MANIFEST:
        make_simple(spec)
    overview = Image.new("RGB", (2400, 2250))
    for i, spec in enumerate(MANIFEST):
        with Image.open(OUT / f"{spec['slug']}-noise-simple.png") as image:
            overview.paste(image.resize((1200, 750), Image.Resampling.LANCZOS),
                           ((i % 2) * 1200, (i // 2) * 750))
    overview.save(OUT / "all-six-simple-comparison.png", icc_profile=model.ICC)
    assert all(digest(path) == original for path, original in originals.items())
    print("Created six simplified PNG/SVG pairs and an overview; all detailed originals are byte-for-byte unchanged.")


if __name__ == "__main__":
    main()
