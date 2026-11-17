"""Descriptive diagnostics derived only from completed out-of-fold predictions."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .config import TARGET
from .verification import verify

MODELS = ['Linear', 'KNN', 'Decision Tree', 'GWR']


def summarize(folder: Path, output: Path) -> dict:
    verify(folder, spatial=True)
    output.mkdir(parents=True, exist_ok=True)
    predictions = pd.read_csv(folder / 'prediksi_uji.csv')
    scores = pd.read_csv(folder / 'metrik.csv').set_index('model')
    folds = pd.read_csv(folder / 'per_wilayah.csv')
    mae = folds.pivot(index='wilayah_uji', columns='model', values='MAE_Rp_m2')
    summary = {
        'n': len(predictions), 'regions': predictions.kab_kota.nunique(),
        'target': predictions[TARGET].describe().to_dict(),
        'negative_predictions': {m: int((predictions[m] < 0).sum()) for m in MODELS},
        'gwr_vs_knn_mae_percent': float(100 * (scores.loc['GWR', 'MAE_Rp_m2'] / scores.loc['KNN', 'MAE_Rp_m2'] - 1)),
        'gwr_vs_knn_rmse_percent': float(100 * (scores.loc['GWR', 'RMSE_Rp_m2'] / scores.loc['KNN', 'RMSE_Rp_m2'] - 1)),
        'gwr_mae_wins': {m: mae.index[mae['GWR'] < mae[m]].tolist() for m in MODELS if m != 'GWR'},
    }
    for model in MODELS:
        error = predictions[TARGET] - predictions[model]
        solo = predictions.kab_kota.eq('Kota Surakarta')
        summary.setdefault('surakarta_share_squared_error', {})[model] = float(np.sum(error[solo] ** 2) / np.sum(error ** 2))
    (output / 'diagnostics.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    fig, axes = plt.subplots(2, 2, figsize=(10, 9), layout='constrained')
    for ax, model in zip(axes.flat, MODELS):
        actual = predictions[TARGET].to_numpy() / 1e6
        estimated = predictions[model].to_numpy() / 1e6
        ax.scatter(actual, estimated, s=20, alpha=.75)
        low, high = min(actual.min(), estimated.min()), max(actual.max(), estimated.max())
        ax.plot([low, high], [low, high], '--', color='gray')
        ax.set_title(model)
        ax.set_xlabel('Aktual (juta Rp/m²)')
        ax.set_ylabel('Prediksi uji (juta Rp/m²)')
        ax.set_aspect('equal', adjustable='box')
    fig.suptitle('127 prediksi out-of-fold; garis putus-putus menunjukkan prediksi tepat')
    fig.savefig(output / 'aktual_prediksi.png', dpi=160)
    fig.savefig(output / 'aktual_prediksi.pdf')
    plt.close(fig)
    return summary
