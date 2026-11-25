"""Hubungan deskriptif tiap fitur baru dengan harga kecamatan selama 2020."""
import argparse
import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
LABELS = {
    "jarak_kampus_km": "Jarak kampus (km)",
    "jarak_wisata_km": "Jarak wisata (km)",
    "elevasi_median_m": "Elevasi median (m)",
    "lereng_median_derajat": "Lereng median (°)",
}


def main(out):
    with (ROOT / "data/processed/akses_medan/fitur.csv").open() as stream:
        features = list(csv.DictReader(stream))
    with (ROOT / "data/harga_tanah_2020.csv").open() as stream:
        prices = {(r["kab_kota"], r["kecamatan"]): float(r["harga_tanah_rata_rata_rp_m2"])
                  for r in csv.DictReader(stream)}
    y = np.array([prices[r["kab_kota"], r["kecamatan"]] for r in features])
    fig, axes = plt.subplots(2, 2, figsize=(8, 6), sharey=True, layout="constrained")
    results = []
    for ax, (variable, label) in zip(axes.flat, LABELS.items()):
        x = np.array([float(r[variable]) for r in features])
        r = np.corrcoef(x, y)[0, 1]
        rho = spearmanr(x, y).statistic
        results.append(dict(variabel=variable, n=len(y), pearson=r, spearman=rho))
        ax.scatter(x, y / 1e6, s=16, color="#20756a", alpha=.65, linewidth=0)
        tw = next(i for i, row in enumerate(features) if row["kecamatan"] == "Tawangmangu")
        ax.scatter(x[tw], y[tw] / 1e6, color="#ba4e24", marker="D", label="Tawangmangu")
        ax.set(yscale="log", xlabel=label, title=f"Pearson {r:.2f}   ·   Spearman {rho:.2f}")
        ax.grid(axis="y", alpha=.2)
    axes[0, 0].legend(frameon=False)
    fig.supylabel("Harga rata-rata 2020 (juta Rp/m², skala log)")
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "akses_medan.png", dpi=220)
    plt.close(fig)
    with (out / "korelasi.csv").open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=results[0])
        writer.writeheader()
        writer.writerows(results)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    main(parser.parse_args().output)
