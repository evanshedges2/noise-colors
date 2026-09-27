"""Create the text-free teaser and labeled answer strip from the calculated colors."""
from pathlib import Path
import json
import os
import tempfile

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "noise-colors-matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from PIL import Image, ImageCms, PngImagePlugin

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figures"
ROWS = json.loads((OUT / "color-calculations.json").read_text(encoding="utf-8"))
LABELS = {
    "pink": ("Pink Noise", ""),
    "white": ("White Noise", ""),
    "brown": ("Brown Noise", "(Red)"),
    "violet": ("Violet Noise", "(Purple)"),
    "grey-hearing": ("Grey Noise", "(Hearing)"),
    "grey-vision": ("Grey Noise", "(Vision)"),
}
CREDIT = "CIE (2019), doi:10.25039/CIE.DS.xvudnb9b. Data and derived figure: CC BY-SA 4.0."


def main():
    assert len(ROWS) == 6
    profile = ImageCms.ImageCmsProfile(ImageCms.createProfile("sRGB")).tobytes()
    teaser = Image.new("RGB", (2400, 600))
    for index, row in enumerate(ROWS):
        teaser.paste(tuple(row["rgb"]), (index * 400, 0, (index + 1) * 400, 600))
    teaser_metadata = PngImagePlugin.PngInfo()
    teaser_metadata.add_text("Title", "Noise colors teaser")
    teaser_metadata.add_text("Copyright", CREDIT)
    teaser.save(OUT / "noise-colors-teaser.png", icc_profile=profile, pnginfo=teaser_metadata)
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.fonttype": "path"})
    fig = plt.figure(figsize=(16, 4), dpi=150)
    artists = []
    for index, row in enumerate(ROWS):
        x = index / 6
        fig.add_artist(Rectangle((x, 0), 1 / 6, 1, transform=fig.transFigure,
                                 facecolor=row["hex"], edgecolor="none", zorder=0))
        ink = "#FFFFFF" if row["slug"] == "grey-vision" else "#302937"
        title, subtitle = LABELS[row["slug"]]
        artists.append(fig.text(x + 1 / 12, .53, title, ha="center", va="center",
                                fontsize=18, color=ink))
        if subtitle:
            artists.append(fig.text(x + 1 / 12, .41, subtitle, ha="center", va="center",
                                    fontsize=14, color=ink))
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for text in artists:
        box = text.get_window_extent(renderer)
        panel = min(int(text.get_position()[0] * 6), 5)
        assert panel * 400 <= box.x0 < box.x1 <= (panel + 1) * 400
        assert 0 < box.y0 < box.y1 < 600
    stem = OUT / "noise-colors-revealed"
    description = (
        "Same colors and order as the unlabeled teaser: pink, white, brown/red, "
        "violet/purple, grey hearing, grey vision. Both grey colors are clipped sRGB approximations."
    )
    fig.savefig(stem.with_suffix(".png"), dpi=150)
    fig.savefig(stem.with_suffix(".svg"), metadata={
        "Title": "Noise colors revealed", "Description": description, "Rights": CREDIT,
    })
    plt.close(fig)
    metadata = PngImagePlugin.PngInfo()
    metadata.add_text("Title", "Noise colors revealed")
    metadata.add_text("Description", description)
    metadata.add_text("Copyright", CREDIT)
    with Image.open(stem.with_suffix(".png")) as source:
        result = source.convert("RGB")
        assert result.size == (2400, 600)
        for index, row in enumerate(ROWS):
            assert result.getpixel((index * 400 + 200, 30)) == tuple(row["rgb"])
        result.save(stem.with_suffix(".png"), icc_profile=profile, pnginfo=metadata)
    print("Created the text-free teaser and labeled PNG/SVG reveal, with the original six colors.")


if __name__ == "__main__":
    main()
