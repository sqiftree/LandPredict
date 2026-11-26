"""Analisis sensitivitas GWR: multikolinearitas, skala target, bandwidth adaptif, dan domain shift."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from .colab_models import (
    DecisionTreeRegressorScratch,
    GWRRegressorScratch,
    KNNRegressorScratch,
    OLSRegressorScratch,
    apply_standardizer,
    fit_standardizer,
    haversine_km,
)
from .config import KEY, ROOT, TARGET
from .data import attach_coordinates, load_observations
from .experiment import metrics
from .provenance import new_audit, save_audit, sha256
from .selection import region_splits

DATA = ROOT / 'data'
ALL7 = [
    'kepadatan_penduduk_proksi',
    'kepadatan_fasum_proksi',
    'built_pct',
    'tree_pct',
    'cropland_pct',
    'jumlah_penduduk',
    'jumlah_fasum_regional',
]
VIF4 = ['built_pct', 'cropland_pct', 'jumlah_penduduk', 'jumlah_fasum_regional']

FIXED_BWS = [5, 10, 15, 25, 40, 60, 80]
ADAP_GAUSS_BWS = [15, 25, 40, 60, 80]
ADAP_BISQ_BWS = [20, 30, 45, 60, 80]
RIDGE_LAMBDAS = [0.0, 0.01, 0.1, 1.0, 10.0]

SURAKARTA = 'Kota Surakarta'
STRAT_SEED = 124


class RidgeGWR:
    """Classic GWR lokal dengan kernel Gaussian/Bisquare dan penalti Ridge tanpa penalti intersep."""

    def __init__(self, bandwidth=20.0, kernel='gaussian', adaptive=False, reg_lambda=0.0):
        self.bandwidth = bandwidth
        self.kernel = kernel
        self.adaptive = adaptive
        self.reg_lambda = reg_lambda
        self.X_train = None
        self.y_train = None
        self.coords_train = None

    def _kernel_weights(self, dists: np.ndarray) -> np.ndarray:
        if self.adaptive:
            k_nn = int(min(max(2, round(self.bandwidth)), len(dists)))
            h = max(float(np.sort(dists)[k_nn - 1]) * 1.000001, 1e-6)
        else:
            h = max(float(self.bandwidth), 1e-6)
        if self.kernel == 'gaussian':
            w = np.exp(-0.5 * (dists / h) ** 2)
        elif self.kernel == 'bisquare':
            w = np.where(dists < h, (1.0 - (dists / h) ** 2) ** 2, 0.0)
        else:
            raise ValueError(f'Kernel tidak dikenal: {self.kernel}')
        if np.sum(w) <= 1e-12:
            return np.ones_like(w)
        return w

    def fit(self, X, y, coords):
        self.X_train = np.asarray(X, dtype=float)
        self.y_train = np.asarray(y, dtype=float)
        self.coords_train = np.asarray(coords, dtype=float)
        return self

    def predict(self, X, coords):
        X_test = np.asarray(X, dtype=float)
        coords_test = np.asarray(coords, dtype=float)
        X_design_train = np.column_stack([np.ones(self.X_train.shape[0]), self.X_train])
        X_design_test = np.column_stack([np.ones(X_test.shape[0]), X_test])
        dist_matrix = haversine_km(
            coords_test[:, 0], coords_test[:, 1],
            self.coords_train[:, 0], self.coords_train[:, 1],
        )
        n_params = X_design_train.shape[1]
        penalty = np.eye(n_params)
        penalty[0, 0] = 0.0
        reg_matrix = self.reg_lambda * penalty + 1e-10 * np.eye(n_params)
        preds = np.zeros(X_test.shape[0], dtype=float)
        for i in range(X_test.shape[0]):
            w_sqrt = np.sqrt(self._kernel_weights(dist_matrix[i]))[:, None]
            X_w = X_design_train * w_sqrt
            y_w = self.y_train * w_sqrt.ravel()
            beta_local = np.linalg.solve(X_w.T @ X_w + reg_matrix, X_w.T @ y_w)
            preds[i] = float(X_design_test[i] @ beta_local)
        return preds


def compute_vif(frame: pd.DataFrame, columns: list[str]) -> dict[str, float]:
    """Hitung Variance Inflation Factor (VIF) deskriptif tiap kolom prediktor."""
    X = frame[columns].to_numpy(dtype=float)
    vifs = {}
    for idx, col in enumerate(columns):
        other = np.delete(X, idx, axis=1)
        design = np.column_stack([np.ones(len(X)), other])
        coef = np.linalg.lstsq(design, X[:, idx], rcond=None)[0]
        ss_tot = float(np.sum((X[:, idx] - np.mean(X[:, idx])) ** 2))
        ss_res = float(np.sum((X[:, idx] - design @ coef) ** 2))
        vifs[col] = ss_tot / ss_res
    return vifs


def load_sensitivity_frame(coordinates: Path = DATA / 'koordinat.csv') -> pd.DataFrame:
    """Muat observasi dasar, variabel pendukung WorldCover/BIG yang terverifikasi, dan koordinat."""
    frame = load_observations()
    support = DATA / 'processed/variabel_pendukung_2020.csv'
    manifest = json.loads((DATA / 'processed/manifest.json').read_text(encoding='utf-8'))
    if sha256(support) != manifest['csv_sha256']:
        raise ValueError('CSV pendukung berbeda dari manifest WorldCover proyek.')
    extended = pd.read_csv(support)
    pd.testing.assert_frame_equal(
        frame.set_index(KEY).sort_index(),
        extended[frame.columns].set_index(KEY).sort_index(),
    )
    extra_cols = [c for c in ALL7 if c not in frame.columns]
    frame = frame.merge(extended[KEY + extra_cols], on=KEY, validate='one_to_one')
    if not np.isfinite(frame[ALL7]).all().all() or (frame[TARGET] <= 0).any():
        raise ValueError('Prediktor harus finite dan harga harus positif.')
    return attach_coordinates(frame, coordinates)[0]


def _make_gwr(kind: str, bw: float, lam: float):
    if kind == 'notebook_fixed':
        return GWRRegressorScratch(bandwidth=bw, kernel='gaussian', adaptive=False, reg_lambda=lam)
    if kind == 'fixed_gauss':
        return RidgeGWR(bandwidth=bw, kernel='gaussian', adaptive=False, reg_lambda=lam)
    if kind == 'adap_gauss':
        return RidgeGWR(bandwidth=bw, kernel='gaussian', adaptive=True, reg_lambda=lam)
    if kind == 'adap_bisq':
        return RidgeGWR(bandwidth=bw, kernel='bisquare', adaptive=True, reg_lambda=lam)
    raise ValueError(f'Varian GWR tidak dikenal: {kind}')


def _fit_predict_model(spec: dict, X_tr: np.ndarray, y_tr_raw: np.ndarray, c_tr: np.ndarray,
                       X_te: np.ndarray, c_te: np.ndarray, log_target: bool,
                       bw: float | None = None, lam: float | None = None) -> np.ndarray:
    sc = fit_standardizer(X_tr)
    xt, xv = apply_standardizer(X_tr, *sc), apply_standardizer(X_te, *sc)
    yt = np.log(y_tr_raw) if log_target else y_tr_raw
    kind = spec['kind']
    if kind == 'ols':
        pred = OLSRegressorScratch(reg_lambda=1e-8).fit(xt, yt).predict(xv)
    elif kind == 'knn':
        pred = KNNRegressorScratch(k=5).fit(xt, yt).predict(xv)
    elif kind == 'tree':
        pred = DecisionTreeRegressorScratch(max_depth=4, min_samples_leaf=3, min_samples_split=6).fit(xt, yt).predict(xv)
    else:
        pred = _make_gwr(kind, bw, lam).fit(xt, yt, c_tr).predict(xv, c_te)
    if log_target:
        if kind == 'notebook_fixed':
            return np.exp(pred)
        return np.exp(np.clip(pred, -50.0, 50.0))
    return pred


def _select_gwr_params(spec: dict, X: np.ndarray, y: np.ndarray, coords: np.ndarray,
                       inner_iter) -> tuple[float, float]:
    best_loss = np.inf
    best_cfg = None
    inner_splits = list(inner_iter)
    for bw in spec['bws']:
        for lam in spec['lambdas']:
            sq_errors = []
            for fit_idx, val_idx in inner_splits:
                pred = _fit_predict_model(
                    spec, X[fit_idx], y[fit_idx], coords[fit_idx],
                    X[val_idx], coords[val_idx], spec['log_target'], bw=bw, lam=lam,
                )
                sq_errors.extend((pred - y[val_idx]) ** 2)
            loss = float(np.sqrt(np.mean(sq_errors)))
            if loss < best_loss:
                best_loss = loss
                best_cfg = (bw, lam)
    return best_cfg


def _format_param(spec: dict, bw: float | None, lam: float | None) -> str:
    kind = spec['kind']
    if kind == 'ols':
        return '1e-08'
    if kind == 'knn':
        return 'k=5'
    if kind == 'tree':
        return 'depth=4'
    unit = 'nn' if 'adap' in kind else 'km'
    return f'bw={bw}{unit};lambda={lam:g}'


def _model_specs(log_target: bool, include_notebook: bool = False, include_unreg: bool = False) -> list[dict]:
    specs = [
        {'name': 'OLS', 'kind': 'ols', 'log_target': log_target},
        {'name': 'KNN (k=5)', 'kind': 'knn', 'log_target': log_target},
        {'name': 'Decision Tree (d=4)', 'kind': 'tree', 'log_target': log_target},
    ]
    if include_notebook:
        specs.append({
            'name': 'GWR Fixed Gauss (lam=1e-3, notebook)', 'kind': 'notebook_fixed',
            'bws': FIXED_BWS, 'lambdas': [1e-3], 'log_target': log_target,
        })
    if include_unreg:
        specs.append({
            'name': 'GWR Fixed Gauss (lam=0)', 'kind': 'fixed_gauss',
            'bws': FIXED_BWS, 'lambdas': [0.0], 'log_target': log_target,
        })
    if not include_notebook:
        specs.append({
            'name': 'GWR Fixed Gauss + Ridge', 'kind': 'fixed_gauss',
            'bws': FIXED_BWS, 'lambdas': RIDGE_LAMBDAS, 'log_target': log_target,
        })
    if include_unreg:
        specs.append({
            'name': 'GWR Adap Gauss (lam=0)', 'kind': 'adap_gauss',
            'bws': ADAP_GAUSS_BWS, 'lambdas': [0.0], 'log_target': log_target,
        })
    specs.extend([
        {
            'name': 'GWR Adap Gauss + Ridge', 'kind': 'adap_gauss',
            'bws': ADAP_GAUSS_BWS, 'lambdas': RIDGE_LAMBDAS, 'log_target': log_target,
        },
        {
            'name': 'GWR Adap Bisq + Ridge', 'kind': 'adap_bisq',
            'bws': ADAP_BISQ_BWS, 'lambdas': RIDGE_LAMBDAS, 'log_target': log_target,
        },
    ])
    return specs


def _evaluate_loro(frame: pd.DataFrame, cols: list[str], specs: list[dict],
                   indices: np.ndarray | None = None) -> tuple[pd.DataFrame, list[dict], dict]:
    sub = frame.iloc[indices].reset_index(drop=True) if indices is not None else frame
    X = sub[cols].to_numpy(dtype=float)
    y = sub[TARGET].to_numpy(dtype=float)
    coords = sub[['lat', 'lon']].to_numpy(dtype=float)
    groups = sub['kab_kota'].to_numpy()
    pred_df = sub[KEY + [TARGET]].copy()
    fold_rows = []
    chosen_params = {}
    for spec in specs:
        mname = spec['name']
        preds = np.full(len(sub), np.nan, dtype=float)
        chosen_params[mname] = {}
        for region, train, test in region_splits(groups):
            bw = lam = None
            if 'bws' in spec:
                inner_iter = ((fit, val) for _, fit, val in region_splits(groups, train))
                bw, lam = _select_gwr_params(spec, X, y, coords, inner_iter)
            chosen_params[mname][region] = _format_param(spec, bw, lam)
            preds[test] = _fit_predict_model(
                spec, X[train], y[train], coords[train],
                X[test], coords[test], spec['log_target'], bw=bw, lam=lam,
            )
            fold_rows.append({
                'model': mname, 'wilayah_uji': region, 'n': int(len(test)),
                'parameter': chosen_params[mname][region],
                **dict(zip(['MAE_Rp_m2', 'RMSE_Rp_m2', 'R2'], metrics(y[test], preds[test]))),
            })
        pred_df[mname] = preds
    return pred_df, fold_rows, chosen_params


def _evaluate_stratified(frame: pd.DataFrame, cols: list[str], specs: list[dict]) -> dict[str, np.ndarray]:
    X = frame[cols].to_numpy(dtype=float)
    y = frame[TARGET].to_numpy(dtype=float)
    coords = frame[['lat', 'lon']].to_numpy(dtype=float)
    groups = frame['kab_kota'].to_numpy()
    outer_cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=STRAT_SEED)
    inner_cv = StratifiedKFold(n_splits=4, shuffle=True, random_state=STRAT_SEED)
    out = {}
    for spec in specs:
        preds = np.full(len(frame), np.nan, dtype=float)
        for train, test in outer_cv.split(X, groups):
            bw = lam = None
            if 'bws' in spec:
                inner_iter = ((train[f], train[v]) for f, v in inner_cv.split(X[train], groups[train]))
                bw, lam = _select_gwr_params(spec, X, y, coords, inner_iter)
            preds[test] = _fit_predict_model(
                spec, X[train], y[train], coords[train],
                X[test], coords[test], spec['log_target'], bw=bw, lam=lam,
            )
        out[spec['name']] = preds
    return out


def run(output: Path = ROOT / 'artifacts/sensitivitas_gwr',
        coordinates: Path = DATA / 'koordinat.csv') -> Path:
    """Jalankan seluruh eksperimen sensitivitas GWR dan simpan hasil terverifikasi."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    candidates = {
        'FIXED_BWS_km': FIXED_BWS,
        'ADAP_GAUSS_BWS_nn': ADAP_GAUSS_BWS,
        'ADAP_BISQ_BWS_nn': ADAP_BISQ_BWS,
        'RIDGE_LAMBDAS': RIDGE_LAMBDAS,
    }
    audit = new_audit(coordinates, candidates)
    audit.update(
        protocol='gwr_sensitivity_v1',
        supporting_sha256=sha256(DATA / 'processed/variabel_pendukung_2020.csv'),
        features_7=ALL7,
        features_4_vif=VIF4,
        inner_selection='pooled RMSE in Rp/m2 on outer training set (no intercept penalty)',
    )
    save_audit(output, audit)
    try:
        frame = load_sensitivity_frame(coordinates)
        audit['vif_7_fitur'] = compute_vif(frame, ALL7)
        audit['vif_4_fitur'] = compute_vif(frame, VIF4)
        groups = frame['kab_kota'].to_numpy()
        y = frame[TARGET].to_numpy(dtype=float)
        no_solo = groups != SURAKARTA
        solo = ~no_solo
        for region, train, test in region_splits(groups):
            audit['outer_folds'].append({
                'test_region': region,
                'train_regions': sorted(set(groups[train])),
                'n_test': int(len(test)),
            })

        # Blok 1: 7-fold LORO (127 kecamatan) lintas fitur & skala target
        loro_specs = [
            ('7_fitur', ALL7, 'log', _model_specs(True, include_notebook=True)),
            ('7_fitur', ALL7, 'linear', _model_specs(False)),
            ('4_fitur_vif', VIF4, 'log', [s for s in _model_specs(True) if s['kind'] != 'adap_bisq']),
            ('4_fitur_vif', VIF4, 'linear', _model_specs(False, include_unreg=True)),
        ]
        summary_rows = []
        selected_summary = {}
        for feat_name, cols, target_scale, specs in loro_specs:
            pred_df, fold_rows, chosen = _evaluate_loro(frame, cols, specs)
            selected_summary[f'{feat_name}__{target_scale}'] = chosen
            for spec in specs:
                mname = spec['name']
                p = pred_df[mname].to_numpy(dtype=float)
                m127 = metrics(y, p)
                m122 = metrics(y[no_solo], p[no_solo])
                mae_solo = float(np.mean(np.abs(y[solo] - p[solo])))
                summary_rows.append({
                    'fitur': feat_name, 'target': target_scale, 'model': mname,
                    'MAE_127': m127[0], 'RMSE_127': m127[1], 'R2_127': m127[2],
                    'prediksi_negatif': int(np.sum(p < 0)),
                    'MAE_122_tanpa_solo': m122[0], 'RMSE_122_tanpa_solo': m122[1],
                    'R2_122_tanpa_solo': m122[2], 'MAE_surakarta': mae_solo,
                })
            if feat_name == '4_fitur_vif' and target_scale == 'linear':
                pred_df.to_csv(output / 'prediksi_4fitur_linear.csv', index=False)
                pd.DataFrame(fold_rows).to_csv(output / 'per_wilayah_4fitur_linear.csv', index=False)
        pd.DataFrame(summary_rows).to_csv(output / 'ringkasan_loro.csv', index=False)

        # Blok 2: 6-fold LORO dilatih ulang tanpa Kota Surakarta (122 kecamatan)
        no_solo_idx = np.flatnonzero(no_solo)
        y_122 = y[no_solo_idx]
        enam_rows = []
        for feat_name, cols, target_scale in [('7_fitur', ALL7, 'log'), ('4_fitur_vif', VIF4, 'linear')]:
            specs = _model_specs(target_scale == 'log')
            pred_122, _, chosen_122 = _evaluate_loro(frame, cols, specs, indices=no_solo_idx)
            selected_summary[f'no_solo_{feat_name}__{target_scale}'] = chosen_122
            for spec in specs:
                mname = spec['name']
                p = pred_122[mname].to_numpy(dtype=float)
                m = metrics(y_122, p)
                enam_rows.append({
                    'fitur': feat_name, 'target': target_scale, 'model': mname,
                    'MAE_122': m[0], 'RMSE_122': m[1], 'R2_122': m[2],
                    'prediksi_negatif': int(np.sum(p < 0)),
                })
        pd.DataFrame(enam_rows).to_csv(output / 'enam_kabupaten_loro.csv', index=False)

        # Blok 3: Stratified 5-Fold CV (pembanding domain shift)
        strat_rows = []
        for feat_name, cols, target_scale in [
            ('7_fitur', ALL7, 'log'),
            ('7_fitur', ALL7, 'linear'),
            ('4_fitur_vif', VIF4, 'linear'),
        ]:
            specs = _model_specs(target_scale == 'log')
            pred_map = _evaluate_stratified(frame, cols, specs)
            for spec in specs:
                mname = spec['name']
                p = pred_map[mname]
                m = metrics(y, p)
                strat_rows.append({
                    'fitur': feat_name, 'target': target_scale, 'model': mname,
                    'MAE_127': m[0], 'RMSE_127': m[1], 'R2_127': m[2],
                    'prediksi_negatif': int(np.sum(p < 0)),
                })
        pd.DataFrame(strat_rows).to_csv(output / 'stratified_cv.csv', index=False)

        audit['selected_parameters'] = selected_summary
        audit['status'] = 'complete'
        save_audit(output, audit)
        verify_sensitivity(output)
    except Exception as exc:
        if audit['status'] == 'running':
            audit['status'] = 'failed'
        audit['error'] = f'{type(exc).__name__}: {exc}'
        save_audit(output, audit)
        raise
    return output


def verify_sensitivity(folder: Path) -> None:
    """Verifikasi integritas dan kecocokan metrik keluaran analisis sensitivitas GWR."""
    if not __debug__:
        raise RuntimeError('Jalankan verifikasi tanpa python -O agar assertions aktif.')
    folder = Path(folder)
    audit = json.loads((folder / 'audit.json').read_text(encoding='utf-8'))
    assert audit.get('status') == 'complete', 'Eksperimen sensitivitas belum selesai.'
    assert audit.get('protocol') == 'gwr_sensitivity_v1'

    source = pd.read_csv(ROOT / 'data/harga_tanah_2020.csv')
    preds = pd.read_csv(folder / 'prediksi_4fitur_linear.csv')
    ringkasan = pd.read_csv(folder / 'ringkasan_loro.csv')
    per_wilayah = pd.read_csv(folder / 'per_wilayah_4fitur_linear.csv')
    enam = pd.read_csv(folder / 'enam_kabupaten_loro.csv')
    strat = pd.read_csv(folder / 'stratified_cv.csv')

    assert len(preds) == 127 and not preds.duplicated(KEY).any()
    pd.testing.assert_frame_equal(
        source[KEY + [TARGET]].sort_values(KEY).reset_index(drop=True),
        preds[KEY + [TARGET]].sort_values(KEY).reset_index(drop=True),
    )
    regions = set(preds['kab_kota'].unique())
    assert len(regions) == 7
    assert len(audit['outer_folds']) == 7
    assert {e['test_region'] for e in audit['outer_folds']} == regions
    for entry in audit['outer_folds']:
        held = entry['test_region']
        assert set(entry['train_regions']) == regions - {held}
        assert entry['n_test'] == int((preds['kab_kota'] == held).sum())

    models_4f = [s['name'] for s in _model_specs(False, include_unreg=True)]
    assert len(per_wilayah) == 7 * len(models_4f)
    y = preds[TARGET].to_numpy(dtype=float)
    no_solo = (preds['kab_kota'] != SURAKARTA).to_numpy()
    solo = ~no_solo
    ring_4f = ringkasan[(ringkasan['fitur'] == '4_fitur_vif') & (ringkasan['target'] == 'linear')].set_index('model')
    assert set(ring_4f.index) == set(models_4f)

    for mname in models_4f:
        p = preds[mname].to_numpy(dtype=float)
        assert np.isfinite(p).all(), f'Prediksi tidak finite: {mname}'
        m127 = metrics(y, p)
        m122 = metrics(y[no_solo], p[no_solo])
        mae_solo = float(np.mean(np.abs(y[solo] - p[solo])))
        row = ring_4f.loc[mname]
        np.testing.assert_allclose(
            [m127[0], m127[1], m127[2], m122[0], m122[1], m122[2], mae_solo],
            [row['MAE_127'], row['RMSE_127'], row['R2_127'],
             row['MAE_122_tanpa_solo'], row['RMSE_122_tanpa_solo'], row['R2_122_tanpa_solo'],
             row['MAE_surakarta']],
            rtol=1e-10,
        )
        assert int(row['prediksi_negatif']) == int(np.sum(p < 0))
        block = per_wilayah[per_wilayah['model'] == mname].set_index('wilayah_uji')
        assert set(block.index) == regions
        for region, grp in preds.groupby('kab_kota'):
            reg_m = metrics(grp[TARGET].to_numpy(dtype=float), grp[mname].to_numpy(dtype=float))
            assert int(block.loc[region, 'n']) == len(grp)
            np.testing.assert_allclose(
                reg_m,
                [block.loc[region, 'MAE_Rp_m2'], block.loc[region, 'RMSE_Rp_m2'], block.loc[region, 'R2']],
                rtol=1e-10,
            )

    assert len(enam) == 12 and np.isfinite(enam[['MAE_122', 'RMSE_122', 'R2_122']]).all().all()
    assert len(strat) == 18 and np.isfinite(strat[['MAE_127', 'RMSE_127', 'R2_127']]).all().all()
    print(f'Valid sensitivitas GWR: {folder} ({len(ringkasan)} baris LORO, {len(enam)} baris 6-kab, {len(strat)} baris Stratified)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--koordinat', type=Path, default=DATA / 'koordinat.csv')
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/sensitivitas_gwr')
    parser.add_argument('--verify', action='store_true', help='Verifikasi folder hasil yang sudah ada tanpa melatih ulang')
    args = parser.parse_args()
    if args.verify:
        verify_sensitivity(args.output)
    else:
        run(args.output, args.koordinat)


if __name__ == '__main__':
    main()
