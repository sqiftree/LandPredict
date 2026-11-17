"""Run the fixed baseline protocol and write out-of-fold results."""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .config import CANDIDATES, FEATURES, KEY, ROOT, TARGET
from .data import attach_coordinates, load_observations
from .models import LocalSingularError, estimate
from .provenance import new_audit, save_audit
from .selection import region_splits, select_parameter


def metrics(actual, predicted):
    return [mean_absolute_error(actual, predicted),
            np.sqrt(mean_squared_error(actual, predicted)), r2_score(actual, predicted)]


def run(coordinates: Path | None = None, output: Path | None = None) -> Path:
    """Evaluate every region exactly once; no target from the outer test is fitted."""
    coordinates = Path(coordinates) if coordinates is not None else None
    frame = load_observations()
    folder = Path(output) if output is not None else ROOT / ('hasil_spasial' if coordinates else 'hasil_awal')
    folder.mkdir(parents=True, exist_ok=True)
    candidates = {name: values for name, values in CANDIDATES.items() if coordinates or name != 'GWR'}
    audit = new_audit(coordinates, candidates)
    save_audit(folder, audit)
    try:
        distances = None
        if coordinates:
            frame, distances = attach_coordinates(frame, coordinates)
        x, y, groups = frame[FEATURES].to_numpy(), frame[TARGET].to_numpy(), frame.kab_kota.to_numpy()
        scores, folds = [], []
        for name, parameters in candidates.items():
            predictions = np.full(len(frame), np.nan)
            for region, train, test in region_splits(groups):
                best = select_parameter(name, parameters, train, groups, x, y, distances, region, audit)
                try:
                    predictions[test] = estimate(name, best, train, test, x, y, distances)
                except LocalSingularError as exc:
                    audit['status'] = 'failed_outer_singular'
                    audit['singular_failures'].append({
                        'stage': 'outer', 'outer_region': region, 'parameter': best, 'error': str(exc),
                    })
                    raise
                if not np.isfinite(predictions[test]).all():
                    raise ValueError(f'Prediksi tidak finite: {name}, {region}')
                audit['outer_folds'].append({
                    'model': name, 'test_region': region, 'parameter': best,
                    'train_regions': sorted(set(groups[train])), 'test_keys': frame.loc[test, KEY].values.tolist(),
                })
                folds.append([name, region, len(test), best, *metrics(y[test], predictions[test])])
            frame[name] = predictions
            scores.append([name, *metrics(y, predictions)])
        pd.DataFrame(scores, columns=['model', 'MAE_Rp_m2', 'RMSE_Rp_m2', 'R2']).to_csv(folder / 'metrik.csv', index=False)
        pd.DataFrame(folds, columns=['model', 'wilayah_uji', 'n', 'parameter', 'MAE_Rp_m2', 'RMSE_Rp_m2', 'R2']).to_csv(folder / 'per_wilayah.csv', index=False)
        frame.to_csv(folder / 'prediksi_uji.csv', index=False)
    except Exception as exc:
        if audit['status'] == 'running':
            audit['status'] = 'failed'
        audit['error'] = f'{type(exc).__name__}: {exc}'
        save_audit(folder, audit)
        raise
    audit['status'] = 'complete'
    save_audit(folder, audit)
    print(pd.read_csv(folder / 'metrik.csv').round(3).to_string(index=False))
    print(f'Hasil tersimpan di {folder}')
    return folder


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--koordinat', type=Path)
    parser.add_argument('--output', type=Path, help='Folder hasil eksperimen')
    args = parser.parse_args()
    run(args.koordinat, args.output)
