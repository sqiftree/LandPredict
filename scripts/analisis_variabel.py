"""Statistik deskriptif dan grafik untuk bagian 6.3 naskah Solo Raya."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tanah.config import FEATURES, KEY, TARGET
from tanah.data import load_observations

LABELS = {
    'kepadatan_penduduk_proksi': ('Kepadatan penduduk', 'jiwa/km²'),
    'kepadatan_fasum_proksi': ('Kepadatan fasum', 'unit/km²'),
    'built_pct': ('Terbangun', '%'),
    'cropland_pct': ('Tanaman budidaya', '%'),
    'tree_pct': ('Tutupan pohon', '%'),
    'jumlah_penduduk': ('Penduduk', 'jiwa'),
    'jumlah_fasum_regional': ('Fasum regional', 'unit'),
    TARGET: ('Harga tanah', 'Rp/m²'),
}
EXTRA = [k for k in LABELS if k not in [*FEATURES, TARGET]]


def save(fig, output, name):
    for ext in ('png', 'pdf'):
        fig.savefig(output / f'{name}.{ext}', dpi=240, bbox_inches='tight')
    plt.close(fig)


def main(output):
    source = ROOT / 'data/processed'
    path = source / 'variabel_pendukung_2020.csv'
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if digest != json.loads((source / 'manifest.json').read_text())['csv_sha256']:
        raise ValueError('CSV berbeda dari manifest sumber.')
    frame = pd.read_csv(path)
    observed = load_observations()
    pd.testing.assert_frame_equal(frame[observed.columns].set_index(KEY).sort_index(),
                                  observed.set_index(KEY).sort_index())
    values = frame[list(LABELS)]
    if not np.isfinite(values).all().all():
        raise ValueError('Nilai analisis tidak lengkap.')
    output.mkdir(parents=True, exist_ok=True)
    stats = values.describe().T.rename(columns={'25%': 'q1', '50%': 'median', '75%': 'q3'})
    stats.insert(0, 'satuan', [LABELS[key][1] for key in stats.index])
    stats.insert(0, 'label', [LABELS[key][0] for key in stats.index])
    stats.to_csv(output / 'statistik_variabel.csv', index_label='variabel')

    # Pearson on average ranks also handles tied observations for Spearman.
    pearson = values.corr()
    spearman = values.rank(method='average').corr()
    reference = pd.read_csv(source / 'korelasi_eksploratif.csv').set_index('variabel')
    for matrix, name in [(pearson, 'pearson'), (spearman, 'spearman')]:
        np.testing.assert_allclose(matrix.loc[reference.index, TARGET], reference[name], atol=1e-12)
    pairs = pd.DataFrame({'pearson': pearson.stack(), 'spearman': spearman.stack(), 'n': len(frame)})
    pairs.to_csv(output / 'korelasi_pasangan.csv', index_label=['variabel_x', 'variabel_y'])

    median = frame.groupby('kab_kota')[EXTRA].median()
    counts = frame.groupby('kab_kota').size()
    median.assign(n=counts).to_csv(output / 'median_per_wilayah.csv')
    regions = [r.split(' ', 1)[1] for r in median.index]
    fig, axes = plt.subplots(1, 5, figsize=(9.4, 3.6), sharey=True, layout='constrained')
    for ax, key in zip(axes, EXTRA):
        series = median[key]
        ax.imshow(series.to_numpy()[:, None], cmap='Blues', aspect='auto', vmin=0, vmax=series.max())
        for i, val in enumerate(series):
            digits = 3 if key == 'kepadatan_fasum_proksi' else 1
            ax.text(0, i, f'{val:.{digits}f}'.replace('.', ','), ha='center', va='center',
                    color='white' if val > .62*series.max() else '#142739')
        ax.set_title(LABELS[key][0].replace(' ', '\n') + '\n(' + LABELS[key][1] + ')', fontsize=10)
        ax.set_xticks([])
        ax.tick_params(length=0)
    axes[0].set_yticks(range(len(regions)), [f'{reg} ({n})' for reg, n in zip(regions, counts)])
    save(fig, output, 'profil_wilayah')

    fig, axes = plt.subplots(3, 2, figsize=(7.6, 7.4), sharey=True, layout='constrained')
    solo = frame.kab_kota.eq('Kota Surakarta')
    for ax, key in zip(axes.flat, EXTRA):
        for mask, color, label in [(~solo, '#176566', 'Enam kabupaten'), (solo, '#ba5029', 'Kota Surakarta')]:
            ax.scatter(frame.loc[mask, key], frame.loc[mask, TARGET]/1e6,
                       s=19, alpha=.75, color=color, label=label, linewidth=0)
        ax.set_xlabel(f'{LABELS[key][0]} ({LABELS[key][1]})')
        ax.grid(axis='y', alpha=.2)
        ax.set_axisbelow(True)
    axes.flat[-1].axis('off')
    axes.flat[-1].legend(*axes.flat[0].get_legend_handles_labels(), loc='center', frameon=False)
    fig.supylabel('Harga rata-rata kecamatan (juta Rp/m²)')
    save(fig, output, 'sebaran_harga')

    fig, ax = plt.subplots(figsize=(7.2, 6.5), layout='constrained')
    # Different triangles give both measures for every pair without repeating a full matrix.
    dual = np.where(np.tril(np.ones(pearson.shape), -1), spearman, pearson).astype(float)
    np.fill_diagonal(dual, np.nan)
    ax.imshow(dual, cmap='RdBu_r', vmin=-1, vmax=1)
    for (i, j), val in np.ndenumerate(dual):
        if i != j:
            ax.text(j, i, f'{val:.2f}'.replace('.', ','), ha='center', va='center',
                    color='white' if abs(val) > .60 else '#172735', fontsize=9)
    labels = [name for name, _ in LABELS.values()]
    ax.set_xticks(range(len(labels)), labels, rotation=43, ha='right')
    ax.set_yticks(range(len(labels)), labels)
    ax.set_title('Segitiga atas: Pearson r     |     Segitiga bawah: Spearman ρ', fontsize=11)
    save(fig, output, 'matriks_korelasi')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    main(parser.parse_args().output)
