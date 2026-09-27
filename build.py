"""Rebuild all article figures using the bundled CIE and ISO data."""
from pathlib import Path
import argparse
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
GENERATORS = (
    "generate_noise_figures.py",
    "generate_simple_noise_figures.py",
    "generate_sensitivity_figures.py",
    "generate_noise_color_reveal.py",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archives-dir", type=Path,
                        help="optionally save detailed and simplified figure ZIPs in this directory")
    args = parser.parse_args()
    for script in GENERATORS:
        print(f"\nBuilding with {script}", flush=True)
        subprocess.run([sys.executable, "-B", str(ROOT / script)], cwd=ROOT, check=True)

    if args.archives_dir is not None:
        destination = args.archives_dir.resolve()
        destination.mkdir(parents=True, exist_ok=True)
        figures = ROOT / "figures"
        simple = figures / "simple"
        groups = (
            ("noise-figures.zip", figures,
             [p for p in figures.rglob("*") if simple not in p.parents]),
            ("noise-figures-simple.zip", simple, list(simple.iterdir())),
        )
        for name, base, paths in groups:
            with zipfile.ZipFile(destination / name, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                for path in sorted(paths):
                    if path.is_file() and path.suffix in {".png", ".svg", ".json", ".csv", ".md"}:
                        archive.write(path, path.relative_to(base))
            print(f"Saved {destination / name}")
    print(f"\nAll figures are in {ROOT / 'figures'}")


if __name__ == "__main__":
    main()
