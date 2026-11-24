"""Replikasi tujuh prediktor dan log-harga dari notebook, tanpa runtime Colab."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from shapely.geometry import Point, shape

from .colab_models import (
    DecisionTreeRegressorScratch, GWRRegressorScratch, KNNRegressorScratch,
    OLSRegressorScratch, apply_standardizer, fit_standardizer,
)
from .config import FEATURES, KEY, ROOT, TARGET
from .data import attach_coordinates, load_observations
from .experiment import metrics
from .provenance import new_audit, save_audit, sha256
from .selection import region_splits
from .verification import verify

DATA = ROOT / 'data'
EXTRA = ['kepadatan_penduduk_proksi', 'kepadatan_fasum_proksi', 'built_pct', 'tree_pct', 'cropland_pct']
PREDICTORS = EXTRA + FEATURES
BANDWIDTHS = [5, 10, 15, 25, 40, 60, 80]
MODELS = ['Linear', 'KNN', 'Decision Tree', 'GWR']


def inputs(coordinates):
    frame = load_observations()
    support = DATA / 'processed/variabel_pendukung_2020.csv'
    manifest = json.loads((DATA / 'processed/manifest.json').read_text())
    if sha256(support) != manifest['csv_sha256']:
        raise ValueError('CSV pendukung berbeda dari manifest WorldCover proyek.')
    extended = pd.read_csv(support)
    pd.testing.assert_frame_equal(frame.set_index(KEY).sort_index(),
                                  extended[frame.columns].set_index(KEY).sort_index())
    frame = frame.merge(extended[KEY + EXTRA], on=KEY, validate='one_to_one')
    if not np.isfinite(frame[PREDICTORS]).all().all() or (frame[TARGET] <= 0).any():
        raise ValueError('Prediktor harus finite dan harga harus positif.')
    return attach_coordinates(frame, coordinates)[0]


def containment(frame):
    # Use the complete geometries exported by the canonical BIG audit.
    polygons = json.loads((ROOT / 'hasil/audit_spasial/solo_raya.geojson').read_text())
    lookup = {tuple(f['properties'][k] for k in KEY): shape(f['geometry']) for f in polygons['features']}
    return [[r.kab_kota, r.kecamatan] for r in frame.itertuples()
            if not lookup[r.kab_kota, r.kecamatan].contains(Point(r.lon, r.lat))]


def run(coordinates, folder):
    folder.mkdir(parents=True, exist_ok=True)
    audit = new_audit(coordinates, {'Linear': [1e-8], 'KNN': [5], 'Decision Tree': [4], 'GWR': BANDWIDTHS})
    audit.update(protocol='colab_log7', features=PREDICTORS, inner_selection='pooled RMSE in Rp/m2',
                 supporting_sha256=sha256(DATA / 'processed/variabel_pendukung_2020.csv'),
                 notebook_sha256=sha256(ROOT / 'notebooks/replikasi_harga_tanah_2020.ipynb'),
                 gwr_ridge=0.001, knn_weights='inverse distance', tree_min_leaf=3, tree_min_split=6)
    save_audit(folder, audit)
    try:
        frame = inputs(coordinates)
        audit['outside_BIG'] = containment(frame)
        groups = frame.kab_kota.to_numpy()
        x = frame[PREDICTORS].to_numpy(dtype=float)
        y = frame[TARGET].to_numpy()
        coords = frame[['lat', 'lon']].to_numpy()
        results, folds = [], []
        for region, train, test in region_splits(groups):
            losses = []
            for bw in BANDWIDTHS:
                errors = []
                for _, fit, valid in region_splits(groups, train):
                    scaler = fit_standardizer(x[fit])
                    model = GWRRegressorScratch(bandwidth=bw).fit(
                        apply_standardizer(x[fit], *scaler), np.log(y[fit]), coords[fit])
                    pred = np.exp(model.predict(apply_standardizer(x[valid], *scaler), coords[valid]))
                    errors.extend((pred - y[valid]) ** 2)
                loss = float(np.sqrt(np.mean(errors)))
                losses.append(loss)
                audit['inner_scores'].append(dict(outer_region=region, bandwidth_km=bw, RMSE_Rp_m2=loss))
            bw = BANDWIDTHS[np.argmin(losses)]
            scaler = fit_standardizer(x[train])
            xt = apply_standardizer(x[train], *scaler)
            xv = apply_standardizer(x[test], *scaler)
            yt = np.log(y[train])
            models = [(OLSRegressorScratch(), 1e-8), (KNNRegressorScratch(), 5),
                      (DecisionTreeRegressorScratch(), 4), (GWRRegressorScratch(bandwidth=bw), bw)]
            for name, (model, param) in zip(MODELS, models):
                if name == 'GWR':
                    log_pred = model.fit(xt, yt, coords[train]).predict(xv, coords[test])
                else:
                    log_pred = model.fit(xt, yt).predict(xv)
                pred = np.exp(log_pred)
                frame.loc[test, name] = pred
                folds.append([name, region, len(test), param, *metrics(y[test], pred)])
                audit['outer_folds'].append(dict(model=name, test_region=region, parameter=param,
                    train_regions=sorted(set(groups[train])), test_keys=frame.loc[test, KEY].values.tolist()))
        cols = ['MAE_Rp_m2', 'RMSE_Rp_m2', 'R2']
        for name in MODELS:
            pred = frame[name]
            results.append([name, *metrics(y, pred), 100 * np.mean(abs(pred - y) / y)])
        frame.to_csv(folder / 'prediksi_uji.csv', index=False)
        pd.DataFrame(results, columns=['model', *cols, 'MAPE_pct']).to_csv(folder / 'metrik.csv', index=False)
        pd.DataFrame(folds, columns=['model', 'wilayah_uji', 'n', 'parameter', *cols]).to_csv(
            folder / 'per_wilayah.csv', index=False)
        audit['status'] = 'complete'
        save_audit(folder, audit)
        verify(folder, spatial=True, colab=True)
    except Exception as exc:
        audit.update(status='failed', error=str(exc))
        save_audit(folder, audit)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--koordinat', type=Path, default=DATA / 'sumber/koordinat_solo_raya.csv')
    parser.add_argument('--output', type=Path, default=ROOT / 'hasil/replikasi_notebook')
    args = parser.parse_args()
    run(args.koordinat, args.output)
