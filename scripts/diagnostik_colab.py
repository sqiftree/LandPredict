"""Gambar paper, VIF deskriptif dan pembanding KNN dengan spesifikasi terkendali."""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tanah.colab import MODELS, PREDICTORS
from tanah.colab_models import KNNRegressorScratch, apply_standardizer, fit_standardizer
from tanah.config import FEATURES, TARGET
from tanah.experiment import metrics
from tanah.selection import region_splits
from tanah.verification import verify


def main(folder):
    verify(folder, spatial=True, colab=True)
    frame = pd.read_csv(folder / 'prediksi_uji.csv')
    folds = pd.read_csv(folder / 'per_wilayah.csv')
    y = frame[TARGET].to_numpy()
    x = frame[FEATURES].to_numpy(dtype=float)
    pred = np.empty(len(y))
    for _, train, test in region_splits(frame.kab_kota.to_numpy()):
        scaler = fit_standardizer(x[train])
        model = KNNRegressorScratch().fit(apply_standardizer(x[train], *scaler), np.log(y[train]))
        pred[test] = np.exp(model.predict(apply_standardizer(x[test], *scaler)))
    controlled = dict(zip(['MAE_Rp_m2', 'RMSE_Rp_m2', 'R2'], metrics(y, pred)))
    df = frame[PREDICTORS]
    vif = {}
    for column in df:
        design = np.column_stack([np.ones(len(df)), df.drop(columns=column)])
        coef = np.linalg.lstsq(design, df[column], rcond=None)[0]
        vif[column] = float(np.sum((df[column] - df[column].mean()) ** 2) /
                            np.sum((df[column] - design @ coef) ** 2))
    solo = frame.kab_kota.eq('Kota Surakarta')
    sse = (frame['GWR'] - y) ** 2
    summary = {'VIF': vif, 'KNN_log_dua_fitur': controlled, 'surakarta_fraksi_SSE_GWR': sse[solo].sum()/sse.sum()}
    (folder / 'diagnostik.json').write_text(json.dumps(summary, indent=2, allow_nan=False))
    pd.concat([frame[['kab_kota', 'kecamatan', TARGET]], pd.Series(pred, name='KNN_log_dua_fitur')], axis=1
              ).to_csv(folder / 'ablasi_knn.csv', index=False)

    fig, (ax, heat) = plt.subplots(1, 2, figsize=(10, 4.4), layout='constrained')
    for mask, color, label in [(~solo, '#216869', 'Enam kabupaten'), (solo, '#bf5429', 'Kota Surakarta')]:
        ax.scatter(y[mask]/1e6, frame.loc[mask, 'KNN']/1e6, s=22, color=color, alpha=.85, label=label)
    ax.plot([0, 12], [0, 12], color='#727578', ls='--', lw=1)
    ax.legend(frameon=False)
    ax.set(xlabel='Aktual (juta Rp/m²)', ylabel='Prediksi uji (juta Rp/m²)', aspect='equal',
           title='a   Prediksi KNN per kecamatan')
    matrix = folds.pivot(index='wilayah_uji', columns='model', values='MAE_Rp_m2')[MODELS] / 1e6
    im = heat.imshow(matrix, cmap='YlGnBu', norm=LogNorm(), aspect='auto')
    heat.set_xticks(range(4), ['Linear', 'KNN', 'Pohon', 'GWR'])
    heat.set_yticks(range(7), [r.split(' ', 1)[1] for r in matrix.index])
    heat.set_title('b   MAE per wilayah (juta Rp/m²)')
    for (i, j), value in np.ndenumerate(matrix.values):
        heat.text(j, i, f'{value:.2f}'.replace('.', ','), ha='center', va='center',
                  color='white' if im.norm(value) > .55 else '#152837')
    for ext in ['pdf', 'png']:
        fig.savefig(folder / f'evaluasi.{ext}', dpi=220, bbox_inches='tight')
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('folder', type=Path)
    main(parser.parse_args().folder)
