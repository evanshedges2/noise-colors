"""Plot sensory response and reciprocal power using the existing color models.

Run from this folder: python3 -B generate_sensitivity_figures.py
Creates PNG/SVG pairs and numeric plot data; never regenerates existing figures.
"""
from pathlib import Path
import hashlib
import json
import sys

sys.dont_write_bytecode = True
import generate_noise_figures as model
import matplotlib.pyplot as plt
from matplotlib.ticker import NullLocator
import numpy as np
from PIL import Image, PngImagePlugin
from scipy.interpolate import PchipInterpolator

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figures" / "sensitivity"
BACKGROUND = "#FAF8FC"
INK = "#302937"
COMPENSATION = "#B23E67"
SOURCES = (
    "Vision: CIE (2019), doi:10.25039/CIE.DS.xvudnb9b, CC BY-SA 4.0. "
    "Hearing: ISO 226:2023, Equation (1) and Table 1, 60 phon. "
    "Hearing sensitivity is an inverse-required-power proxy, not a linear loudness response."
)


def datasets():
    wavelength = model.WAVELENGTHS.copy()
    vision_response = model.CMF[:, 1].copy()
    assert wavelength[np.argmax(vision_response)] == 555
    assert vision_response.max() == 1

    iso_frequencies = np.array(model.ISO226["frequency_hz"], dtype=float)
    # Include every ISO node so normalization is anchored to the actual contour.
    frequency = np.unique(np.r_[np.geomspace(20, 12500, 1800), iso_frequencies])
    interpolate_spl = PchipInterpolator(np.log(iso_frequencies), model.iso226_spl())
    spl = interpolate_spl(np.log(frequency))
    reference_spl = float(spl.min())
    hearing_response = 10 ** ((reference_spl - spl) / 10)
    assert abs(float(interpolate_spl(np.log(1000))) - 60) < 1e-10

    records = [
        dict(slug="vision", title="Vision", color="#267B60", x=wavelength,
             sensitivity=vision_response, compensation=1 / vision_response,
             xlabel="Wavelength (nm)", sensitivity_title="Photopic sensitivity",
             peak_x=555., peak_label="555", xticks=[400, 450, 500, 555, 600, 650, 700],
             xticklabels=["400", "450", "500", "555", "600", "650", "700"],
             source="CIE 1931 2-degree observer: y-bar(lambda) = V(lambda)",
             reference="555 nm; V = 1"),
        dict(slug="hearing", title="Hearing", color="#704BA0", x=frequency,
             sensitivity=hearing_response, compensation=1 / hearing_response,
             xlabel="Audio frequency (Hz, log scale)", sensitivity_title="Sensitivity proxy at 60 phon",
             peak_x=float(frequency[np.argmax(hearing_response)]), peak_label="3.15k",
             xticks=[20, 100, 1000, 3150, 12500],
             xticklabels=["20", "100", "1k", "3.15k", "12.5k"],
             source="ISO 226:2023 Eq. (1), Table 1; PCHIP of SPL versus log frequency",
             reference=f"3150 Hz; 60-phon SPL = {reference_spl:.12f} dB",
             spl=spl),
    ]
    # Re-express both plotted compensation curves with the existing display model.
    # Reference choices must cancel under common-channel color normalization.
    assert model.calculate(records[0]["compensation"])["hex"] == "#7C00FF"
    mapped_audio = np.clip(model.audio_at_wavelength(wavelength), 20, 12500)
    mapped_compensation = 10 ** ((interpolate_spl(np.log(mapped_audio)) - reference_spl) / 10)
    mapped_spectrum = mapped_compensation * model.MAPPING_Q * mapped_audio / wavelength
    assert model.calculate(mapped_spectrum)["hex"] == "#FF0052"
    for record in records:
        assert np.all(np.isfinite(record["compensation"]))
        assert np.allclose(record["sensitivity"] * record["compensation"], 1)
        assert np.isclose(record["sensitivity"].max(), 1)
        assert np.isclose(record["compensation"].min(), 1)
    return records


def draw_row(fig, record, row, count):
    # Coordinates are local to each row; combined and separate artwork match.
    height = 1 / count
    offset = 1 - (row + 1) * height
    fig.text(.5, offset + .935 * height, record["title"], ha="center", va="center",
             fontsize=33, color=INK, fontproperties=model.SERIF)
    for column, kind in enumerate(["sensitivity", "compensation"]):
        ax = fig.add_axes([.105 + column * .48, offset + .205 * height,
                           .355, .585 * height], facecolor=BACKGROUND)
        color = record["color"] if kind == "sensitivity" else COMPENSATION
        values = record[kind]
        if record["slug"] == "hearing":
            ax.set_xscale("log")
        ax.set_xlim(float(record["x"][0]), float(record["x"][-1]))
        ax.set_xticks(record["xticks"])
        ax.set_xticklabels(record["xticklabels"])
        ax.xaxis.set_minor_locator(NullLocator())
        if kind == "sensitivity":
            ax.set_ylim(0, 1.08)
            ax.set_yticks([0, .25, .5, .75, 1])
            ax.set_yticklabels(["0", "0.25", "0.50", "0.75", "1.00"])
            ax.set_ylabel("Relative sensitivity", fontsize=20, labelpad=15, color=INK)
            ax.set_title(record["sensitivity_title"], fontsize=22, pad=23, color=INK)
        else:
            upper_exponent = int(np.ceil(np.log10(values.max())))
            ax.set_yscale("log")
            ax.set_ylim(.8, 10. ** upper_exponent)
            exponents = np.arange(upper_exponent + 1)
            ax.set_yticks(10. ** exponents)
            ax.set_yticklabels(["1" if n == 0 else rf"$10^{{{n}}}$" for n in exponents])
            ax.yaxis.set_minor_locator(NullLocator())
            ax.set_ylabel("Relative power (log scale)", fontsize=20, labelpad=15, color=INK)
            ax.set_title("Compensating power", fontsize=22, pad=23, color=INK)
        for edge in ["top", "right"]:
            ax.spines[edge].set_visible(False)
        for edge in ["left", "bottom"]:
            ax.spines[edge].set_color(INK)
            ax.spines[edge].set_alpha(.35)
        ax.tick_params(axis="both", colors=INK, labelsize=16, length=0, pad=11)
        ax.grid(axis="y", color=INK, alpha=.10, linewidth=.8)
        ax.set_axisbelow(True)
        ax.plot(record["x"], values, color=color, linewidth=3.2, solid_capstyle="round")
        ax.axvline(record["peak_x"], color=record["color"], alpha=.3,
                   linewidth=1.2, linestyle=(0, (3, 4)))
        ax.scatter([record["peak_x"]], [1.], color=color, s=37, zorder=4)
        ax.set_xlabel(record["xlabel"], fontsize=20, labelpad=18, color=INK)


def save_figure(records, stem):
    count = len(records)
    fig = plt.figure(figsize=(16, 7.8 * count), dpi=150, facecolor=BACKGROUND)
    for row, record in enumerate(records):
        draw_row(fig, record, row, count)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    text_artists = list(fig.texts)
    for ax in fig.axes:
        text_artists.extend([ax.title, ax.xaxis.label, ax.yaxis.label,
                             *ax.get_xticklabels(), *ax.get_yticklabels()])
    for artist in text_artists:
        box = artist.get_window_extent(renderer)
        assert 0 <= box.x0 < box.x1 <= fig.bbox.width, (stem, artist.get_text(), box)
        assert 0 <= box.y0 < box.y1 <= fig.bbox.height, (stem, artist.get_text(), box)
    title = " / ".join(record["title"] for record in records) + ": sensitivity and compensation"
    description = ("Left: sensitivity normalized to a maximum of 1. Right: reciprocal power, "
                   "minimum 1, on a logarithmic vertical axis. Vertical guides mark peak sensitivity. "
                   "The hearing panel is in audio frequency, before the audio-to-light mapping. " + SOURCES)
    path = OUT / stem
    fig.savefig(path.with_suffix(".png"), dpi=150, facecolor=BACKGROUND)
    fig.savefig(path.with_suffix(".svg"), facecolor=BACKGROUND, metadata={
        "Title": title, "Description": description,
        "Creator": "Matplotlib; existing CIE/ISO color models",
        "Rights": "Figure: CC BY-SA 4.0. " + SOURCES,
    })
    plt.close(fig)
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Title", title)
    metadata.add_text("Description", description)
    metadata.add_text("Copyright", "Figure: CC BY-SA 4.0. " + SOURCES)
    with Image.open(path.with_suffix(".png")) as source:
        image = source.convert("RGB")
        assert image.size == (2400, 1170 * count)
        image.save(path.with_suffix(".png"), icc_profile=model.ICC, pnginfo=metadata)
    with Image.open(path.with_suffix(".png")) as check:
        assert check.info.get("icc_profile")


def main():
    # Guard the other figure sets without scanning virtual environments or Git.
    originals = {path: hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in (ROOT / "figures").rglob("*")
                 if path.is_file() and OUT not in path.parents}
    OUT.mkdir(exist_ok=True)
    records = datasets()
    for record in records:
        save_figure([record], record["slug"] + "-sensitivity-compensation")
        columns = [record["x"], record["sensitivity"], record["compensation"]]
        header = "wavelength_nm" if record["slug"] == "vision" else "audio_frequency_hz"
        header += ",relative_sensitivity,relative_compensating_power"
        if "spl" in record:
            columns.append(record["spl"])
            header += ",equal_loudness_spl_db"
        np.savetxt(OUT / (record["slug"] + "-sensitivity-data.csv"), np.column_stack(columns),
                   delimiter=",", header=header, comments="", fmt="%.12g")
    save_figure(records, "vision-and-hearing-sensitivity")
    notes = [{key: record[key] for key in ["slug", "source", "reference", "peak_x"]}
             | {"maximum_compensating_power": float(record["compensation"].max())}
             for record in records]
    (OUT / "plot-calculations.json").write_text(json.dumps(notes, indent=2) + "\n", encoding="utf-8")
    assert all(hashlib.sha256(path.read_bytes()).hexdigest() == digest
               for path, digest in originals.items())
    print(json.dumps(notes, indent=2))
    print("Saved three PNG/SVG pairs; other figure sets are unchanged.")


if __name__ == "__main__":
    main()
