"""Diagnostik statistik dan spasial lanjutan untuk menjawab audit metodologis paper.

Mencakup:
1. Interval kepercayaan Bootstrap Blok Kabupaten/Kota (B=10.000) & metrik ganda (127 vs 122 kec. + Surakarta).
2. Area of Applicability (AoA) & Dissimilarity Index out-of-fold (Meyer & Pebesma, 2021).
3. Global Moran's I & Local Moran's I (LISA) atas residual out-of-fold + peta residual spasial.
4. Audit prediksi negatif, koreksi retransformasi Duan smearing, & model positif Quasi-Poisson QMLE.
5. Gerbang pra-pemodelan VIF dalam-lipatan, local condition number (Wheeler, 2007), & benchmark adil setara.
6. Uji sensitivitas titik representatif kecamatan (PointOnSurface BIG, Centroid BIG, BPS/HDX, GADM/Notebook).
"""
import argparse
import gzip
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Polygon as MplPolygon
from matplotlib.collections import PatchCollection
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeRegressor

from .colab_models import KNNRegressorScratch, apply_standardizer, fit_standardizer, haversine_km
from .config import FEATURES, KEY, ROOT, TARGET
from .coordinates import norm, region as norm_region
from .experiment import metrics
from .provenance import new_audit, save_audit, sha256
from .selection import region_splits
from .sensitivity import (
    ADAP_GAUSS_BWS,
    ALL7,
    DATA,
    FIXED_BWS,
    RIDGE_LAMBDAS,
    SURAKARTA,
    VIF4,
    RidgeGWR,
    compute_vif,
    load_sensitivity_frame,
)

SEED = 124
BOOT_REPS = 10_000
MORAN_PERMS = 9_999
LISA_PERMS = 999


def _load_solo_polygons() -> dict[tuple[str, str], list[list[list[float]]]]:
    """Muat geometri poligon penuh 127 kecamatan Solo Raya dari arsip BIG."""
    df_keys = pd.read_csv(DATA / 'harga_tanah_2020.csv')[KEY]
    names = {(norm_region(k), norm(c)): (k, c) for k, c in df_keys.itertuples(index=False)}
    replacements = {}
    for row in pd.read_csv(DATA / 'padanan_nama.csv').itertuples(index=False):
        replacements[(norm_region(row.kab_sumber), norm(row.kec_sumber))] = (
            norm_region(row.kab_kota), norm(row.kecamatan)
        )
    with gzip.open(DATA / 'jawa_tengah_big.geojson.gz', 'rt', encoding='utf-8') as f:
        gj = json.load(f)
    polys: dict[tuple[str, str], list[list[list[float]]]] = {}
    for feat in gj['features']:
        props = feat['properties']
        raw_k = (norm_region(props['wadmkk']), norm(props['wadmkc']))
        canon = names.get(replacements.get(raw_k, raw_k))
        if canon is None:
            continue
        geom = feat['geometry']
        rings_list = polys.setdefault(canon, [])
        if geom['type'] == 'Polygon':
            rings_list.append(geom['coordinates'])
        elif geom['type'] == 'MultiPolygon':
            rings_list.extend(geom['coordinates'])
    if len(polys) != 127:
        raise ValueError(f'Poligon Solo Raya harus 127 kecamatan, ditemukan: {len(polys)}')
    return polys


def _polygon_centroid_wgs84(multipoly: list[list[list[float]]]) -> tuple[float, float]:
    """Hitung centroid luas-tertimbang planar lokal (ekuivalen metrik Solo Raya) lalu kembalikan (lat, lon)."""
    lat0 = -7.6 * math.pi / 180.0
    cos0 = math.cos(lat0)
    scale = 111_320.0
    total_area = 0.0
    cx_acc = 0.0
    cy_acc = 0.0
    fallback_pts = []
    for poly in multipoly:
        for r_idx, ring in enumerate(poly):
            pts = np.asarray(ring, dtype=float)
            fallback_pts.append(pts[:, :2])
            x = (pts[:, 0] - 110.8) * cos0 * scale
            y = (pts[:, 1] + 7.6) * scale
            x0, y0 = x[:-1], y[:-1]
            x1, y1 = x[1:], y[1:]
            cross = x0 * y1 - x1 * y0
            signed_area = 0.5 * float(np.sum(cross))
            if abs(signed_area) < 1e-6:
                continue
            cx = float(np.sum((x0 + x1) * cross)) / (6.0 * signed_area)
            cy = float(np.sum((y0 + y1) * cross)) / (6.0 * signed_area)
            weight = abs(signed_area) * (1.0 if r_idx == 0 else -1.0)
            total_area += weight
            cx_acc += cx * weight
            cy_acc += cy * weight
    if abs(total_area) < 1e-6:
        all_pts = np.vstack(fallback_pts)
        return float(np.mean(all_pts[:, 1])), float(np.mean(all_pts[:, 0]))
    lon = 110.8 + (cx_acc / total_area) / (cos0 * scale)
    lat = -7.6 + (cy_acc / total_area) / scale
    return float(lat), float(lon)


def build_queen_weights(keys: list[tuple[str, str]],
                        polys: dict[tuple[str, str], list[list[list[float]]]]) -> tuple[np.ndarray, np.ndarray]:
    """Bangun matriks kontiguitas Queen (biner A dan row-standardized W) atas 127 poligon BIG."""
    n = len(keys)
    vertex_owner: dict[tuple[int, int], set[int]] = {}
    for idx, key in enumerate(keys):
        for poly in polys[key]:
            for ring in poly:
                for pt in ring:
                    v = (round(float(pt[0]) * 1_000_000), round(float(pt[1]) * 1_000_000))
                    vertex_owner.setdefault(v, set()).add(idx)
    adj = np.zeros((n, n), dtype=float)
    for owners in vertex_owner.values():
        if len(owners) > 1:
            olist = list(owners)
            for i in range(len(olist)):
                for j in range(i + 1, len(olist)):
                    u, v = olist[i], olist[j]
                    adj[u, v] = 1.0
                    adj[v, u] = 1.0
    deg = adj.sum(axis=1)
    if np.any(deg == 0):
        raise ValueError('Ditemukan kecamatan tanpa tetangga Queen pada poligon Solo Raya.')
    w = adj / deg[:, None]
    return adj, w


def moran_and_lisa(residuals: np.ndarray, w: np.ndarray, seed: int = SEED) -> dict:
    """Hitung Global Moran's I (uji permutasi) dan klaster Local Moran's I (Anselin, 1995)."""
    rng = np.random.default_rng(seed)
    n = len(residuals)
    z = residuals - np.mean(residuals)
    denom = float(np.sum(z ** 2))
    s0 = float(np.sum(w))
    wz = w @ z
    i_obs = float((n / s0) * (z @ wz) / denom)
    ei = -1.0 / (n - 1)

    perm_i = np.empty(MORAN_PERMS, dtype=float)
    for b in range(MORAN_PERMS):
        zp = rng.permutation(z)
        perm_i[b] = (n / s0) * (zp @ (w @ zp)) / denom
    z_score = float((i_obs - np.mean(perm_i)) / np.std(perm_i, ddof=1))
    p_perm = float((np.sum(np.abs(perm_i - ei) >= abs(i_obs - ei)) + 1) / (MORAN_PERMS + 1))

    m2 = denom / n
    local_i = (z / m2) * wz
    p_local = np.empty(n, dtype=float)
    for idx in range(n):
        others = np.delete(z, idx)
        w_row = np.delete(w[idx], idx)
        k_nb = int(np.sum(w_row > 0))
        nb_weights = w_row[w_row > 0]
        # Conditional random permutations of non-focal values on focal neighbor slots
        draws = np.array([others[rng.choice(n - 1, size=k_nb, replace=False)] for _ in range(LISA_PERMS)])
        sim_lag = draws @ nb_weights
        sim_i = (z[idx] / m2) * sim_lag
        p_local[idx] = (np.sum(np.abs(sim_i) >= abs(local_i[idx])) + 1) / (LISA_PERMS + 1)

    labels = np.full(n, 'NS', dtype=object)
    sig = p_local < 0.05
    labels[sig & (z > 0) & (wz > 0)] = 'HH'
    labels[sig & (z < 0) & (wz < 0)] = 'LL'
    labels[sig & (z > 0) & (wz < 0)] = 'HL'
    labels[sig & (z < 0) & (wz > 0)] = 'LH'
    return {
        'moran_i': i_obs,
        'expected_i': ei,
        'z_score': z_score,
        'p_perm': p_perm,
        'n_sig_total': int(np.sum(sig)),
        'n_HH': int(np.sum(labels == 'HH')),
        'n_LL': int(np.sum(labels == 'LL')),
        'n_HL': int(np.sum(labels == 'HL')),
        'n_LH': int(np.sum(labels == 'LH')),
        'local_i': local_i,
        'p_local': p_local,
        'labels': labels,
    }


def block_bootstrap_summary(y: np.ndarray, groups: np.ndarray,
                            pred_dict: dict[str, np.ndarray],
                            ref_model: str, seed: int = SEED) -> list[dict]:
    """Bootstrap blok kabupaten/kota (B=10.000) untuk MAE, RMSE, dan selisih berpasangan."""
    rng = np.random.default_rng(seed)
    unique_regions = np.array(sorted(set(groups)))
    reg_idx = {r: np.flatnonzero(groups == r) for r in unique_regions}
    non_solo_regions = np.array([r for r in unique_regions if r != SURAKARTA])
    solo_mask = groups == SURAKARTA
    non_solo_mask = ~solo_mask

    g_all = len(unique_regions)
    g_ns = len(non_solo_regions)
    draws_all = rng.integers(0, g_all, size=(BOOT_REPS, g_all))
    draws_ns = rng.integers(0, g_ns, size=(BOOT_REPS, g_ns))

    # Precompute per-region sufficient statistics: n_r, sum_abs_r, sum_sq_r
    n_r = np.array([len(reg_idx[r]) for r in unique_regions], dtype=float)
    ns_pos = np.array([np.where(unique_regions == r)[0][0] for r in non_solo_regions])

    stats_by_model = {}
    for mname, p in pred_dict.items():
        err = y - p
        s_abs = np.array([np.sum(np.abs(err[reg_idx[r]])) for r in unique_regions], dtype=float)
        s_sq = np.array([np.sum(err[reg_idx[r]] ** 2) for r in unique_regions], dtype=float)
        tot_n_all = np.sum(n_r[draws_all], axis=1)
        mae_b_all = np.sum(s_abs[draws_all], axis=1) / tot_n_all
        rmse_b_all = np.sqrt(np.sum(s_sq[draws_all], axis=1) / tot_n_all)

        n_r_ns = n_r[ns_pos]
        s_abs_ns = s_abs[ns_pos]
        s_sq_ns = s_sq[ns_pos]
        tot_n_ns = np.sum(n_r_ns[draws_ns], axis=1)
        mae_b_ns = np.sum(s_abs_ns[draws_ns], axis=1) / tot_n_ns
        rmse_b_ns = np.sqrt(np.sum(s_sq_ns[draws_ns], axis=1) / tot_n_ns)
        stats_by_model[mname] = (mae_b_all, rmse_b_all, mae_b_ns, rmse_b_ns)

    ref_mae_all, _, ref_mae_ns, _ = stats_by_model[ref_model]
    rows = []
    for mname, p in pred_dict.items():
        m127 = metrics(y, p)
        m122 = metrics(y[non_solo_mask], p[non_solo_mask])
        err_solo = y[solo_mask] - p[solo_mask]
        mae_solo = float(np.mean(np.abs(err_solo)))
        rmse_solo = float(np.sqrt(np.mean(err_solo ** 2)))
        sse_share_solo = float(np.sum(err_solo ** 2) / np.sum((y - p) ** 2))

        mae_b_all, rmse_b_all, mae_b_ns, rmse_b_ns = stats_by_model[mname]
        diff_all = mae_b_all - ref_mae_all
        diff_ns = mae_b_ns - ref_mae_ns
        rows.append({
            'model': mname,
            'MAE_127': m127[0],
            'MAE_127_ci_lo': float(np.quantile(mae_b_all, 0.025)),
            'MAE_127_ci_hi': float(np.quantile(mae_b_all, 0.975)),
            'RMSE_127': m127[1],
            'RMSE_127_ci_lo': float(np.quantile(rmse_b_all, 0.025)),
            'RMSE_127_ci_hi': float(np.quantile(rmse_b_all, 0.975)),
            'R2_127': m127[2],
            'delta_MAE_127_vs_ref': float(m127[0] - metrics(y, pred_dict[ref_model])[0]),
            'delta_MAE_127_ci_lo': float(np.quantile(diff_all, 0.025)),
            'delta_MAE_127_ci_hi': float(np.quantile(diff_all, 0.975)),
            'MAE_122_tanpa_solo': m122[0],
            'MAE_122_ci_lo': float(np.quantile(mae_b_ns, 0.025)),
            'MAE_122_ci_hi': float(np.quantile(mae_b_ns, 0.975)),
            'RMSE_122_tanpa_solo': m122[1],
            'RMSE_122_ci_lo': float(np.quantile(rmse_b_ns, 0.025)),
            'RMSE_122_ci_hi': float(np.quantile(rmse_b_ns, 0.975)),
            'R2_122_tanpa_solo': m122[2],
            'delta_MAE_122_vs_ref': float(m122[0] - metrics(y[non_solo_mask], pred_dict[ref_model][non_solo_mask])[0]),
            'delta_MAE_122_ci_lo': float(np.quantile(diff_ns, 0.025)),
            'delta_MAE_122_ci_hi': float(np.quantile(diff_ns, 0.975)),
            'MAE_surakarta': mae_solo,
            'RMSE_surakarta': rmse_solo,
            'pangsa_SSE_surakarta_pct': 100.0 * sse_share_solo,
        })
    return rows


def compute_aoa_loko(frame: pd.DataFrame, cols: list[str]) -> tuple[pd.DataFrame, dict]:
    """Hitung Dissimilarity Index (DI) & Area of Applicability (Meyer & Pebesma, 2021) murni out-of-fold."""
    X = frame[cols].to_numpy(dtype=float)
    groups = frame['kab_kota'].to_numpy()
    di_test = np.full(len(frame), np.nan, dtype=float)
    thresh_test = np.full(len(frame), np.nan, dtype=float)

    for _, train, test in region_splits(groups):
        sc = fit_standardizer(X[train])
        xt = apply_standardizer(X[train], *sc)
        xv = apply_standardizer(X[test], *sc)
        dmat_tr = np.sqrt(np.sum((xt[:, None, :] - xt[None, :, :]) ** 2, axis=2))
        iu = np.triu_indices(len(xt), k=1)
        d_bar = float(np.mean(dmat_tr[iu]))

        # Inner LOKO nearest-neighbor distance among training observations
        di_inner = np.empty(len(train), dtype=float)
        tr_groups = groups[train]
        for reg_in in np.unique(tr_groups):
            val_m = tr_groups == reg_in
            fit_m = ~val_m
            d_sub = np.sqrt(np.sum((xt[val_m][:, None, :] - xt[fit_m][None, :, :]) ** 2, axis=2))
            di_inner[val_m] = np.min(d_sub, axis=1) / d_bar

        q25, q75 = np.quantile(di_inner, [0.25, 0.75])
        tau = float(q75 + 1.5 * (q75 - q25))
        d_te = np.sqrt(np.sum((xv[:, None, :] - xt[None, :, :]) ** 2, axis=2))
        di_test[test] = np.min(d_te, axis=1) / d_bar
        thresh_test[test] = tau

    outside = di_test > thresh_test
    out_df = frame[KEY + [TARGET]].copy()
    out_df['DI'] = di_test
    out_df['ambang_AoA'] = thresh_test
    out_df['di_luar_AoA'] = outside
    solo = frame['kab_kota'].to_numpy() == SURAKARTA
    summary = {
        'n_total': int(len(frame)),
        'n_luar_AoA': int(np.sum(outside)),
        'pct_luar_AoA': float(100.0 * np.mean(outside)),
        'n_solo_luar_AoA': int(np.sum(outside & solo)),
        'n_nonsolo_luar_AoA': int(np.sum(outside & ~solo)),
        'median_DI_solo': float(np.median(di_test[solo])),
        'max_DI_solo': float(np.max(di_test[solo])),
        'median_DI_nonsolo': float(np.median(di_test[~solo])),
        'max_DI_nonsolo': float(np.max(di_test[~solo])),
        'median_ambang': float(np.median(thresh_test)),
    }
    return out_df, summary


def fit_predict_poisson_qmle(X_tr: np.ndarray, y_tr: np.ndarray, X_te: np.ndarray,
                             weights_matrix: np.ndarray | None = None,
                             reg_lambda: float = 0.01) -> np.ndarray:
    """Quasi-Poisson QMLE (log-link pada skala asli y > 0) dengan penalti Ridge non-intersep."""
    y_scale = float(np.mean(y_tr))
    ys = y_tr / y_scale
    Xd_tr = np.column_stack([np.ones(len(X_tr)), X_tr])
    Xd_te = np.column_stack([np.ones(len(X_te)), X_te])
    p = Xd_tr.shape[1]
    pen = np.eye(p) * max(reg_lambda, 1e-8)
    pen[0, 0] = 0.0

    def _solve_single(w_vec: np.ndarray) -> np.ndarray:
        w = w_vec / np.mean(w_vec)
        beta = np.zeros(p, dtype=float)
        beta[0] = math.log(max(float(np.sum(w * ys) / np.sum(w)), 1e-8))
        for _ in range(35):
            eta = np.clip(Xd_tr @ beta, -12.0, 12.0)
            mu = np.exp(eta)
            grad = Xd_tr.T @ (w * (mu - ys)) + pen @ beta
            if float(np.max(np.abs(grad))) < 1e-7:
                break
            hess = (Xd_tr.T * (w * mu)) @ Xd_tr + pen + 1e-8 * np.eye(p)
            step = np.linalg.solve(hess, grad)
            # Backtracking line search on penalized deviance objective
            obj0 = float(np.sum(w * (mu - ys * eta)) + 0.5 * (beta @ (pen @ beta)))
            alpha = 1.0
            while alpha > 1e-4:
                cand = beta - alpha * step
                eta_c = np.clip(Xd_tr @ cand, -12.0, 12.0)
                obj_c = float(np.sum(w * (np.exp(eta_c) - ys * eta_c)) + 0.5 * (cand @ (pen @ cand)))
                if obj_c <= obj0 + 1e-9:
                    beta = cand
                    break
                alpha *= 0.5
            else:
                break
        return beta

    if weights_matrix is None:
        beta_g = _solve_single(np.ones(len(X_tr), dtype=float))
        return y_scale * np.exp(np.clip(Xd_te @ beta_g, -12.0, 12.0))

    preds = np.empty(len(X_te), dtype=float)
    for i in range(len(X_te)):
        beta_i = _solve_single(weights_matrix[i])
        preds[i] = y_scale * math.exp(float(np.clip(Xd_te[i] @ beta_i, -12.0, 12.0)))
    return preds


def _gaussian_weights(coords_te: np.ndarray, coords_tr: np.ndarray, bw: float, adaptive: bool = False) -> np.ndarray:
    dmat = haversine_km(coords_te[:, 0], coords_te[:, 1], coords_tr[:, 0], coords_tr[:, 1])
    if adaptive:
        k_nn = int(min(max(2, round(bw)), dmat.shape[1]))
        h = np.maximum(np.sort(dmat, axis=1)[:, k_nn - 1:k_nn] * 1.000001, 1e-6)
    else:
        h = max(float(bw), 1e-6)
    w = np.exp(-0.5 * (dmat / h) ** 2)
    row_sums = np.sum(w, axis=1, keepdims=True)
    w = np.where(row_sums <= 1e-12, 1.0, w)
    return w


def evaluate_target_treatments(frame: pd.DataFrame) -> list[dict]:
    """Evaluasi konsisten skala linear, potong nol, log naif, koreksi Duan smearing, dan Poisson QMLE."""
    groups = frame['kab_kota'].to_numpy()
    y = frame[TARGET].to_numpy(dtype=float)
    log_y = np.log(y)
    coords = frame[['lat', 'lon']].to_numpy(dtype=float)
    solo = groups == SURAKARTA
    rows = []

    for feat_tag, cols in [('2_fitur_utama', FEATURES), ('4_fitur_vif', VIF4), ('7_fitur_pendukung', ALL7)]:
        X = frame[cols].to_numpy(dtype=float)
        # 1. Global OLS/Ridge (lambda=0.01 pada 7 fitur agar stabil numerik, 1e-8 pada 2 & 4 fitur)
        lam_lin = 0.01 if len(cols) == 7 else 1e-8
        p_lin = np.empty(len(y))
        p_log_naive = np.empty(len(y))
        p_log_duan = np.empty(len(y))
        z_pred_oof = np.empty(len(y))
        p_pois = np.empty(len(y))

        # GWR Fixed Ridge (tuning bw in [10, 20, 40, 80], lam in [0.01, 0.1, 1.0, 10.0])
        gwr_lin = np.empty(len(y))
        gwr_log_naive = np.empty(len(y))
        gwr_log_duan = np.empty(len(y))
        gwr_z_oof = np.empty(len(y))
        gwr_pois = np.empty(len(y))

        for _, train, test in region_splits(groups):
            sc = fit_standardizer(X[train])
            xt, xv = apply_standardizer(X[train], *sc), apply_standardizer(X[test], *sc)
            Xd_tr = np.column_stack([np.ones(len(xt)), xt])
            Xd_te = np.column_stack([np.ones(len(xv)), xv])
            pen = np.eye(Xd_tr.shape[1]) * lam_lin
            pen[0, 0] = 0.0

            beta_lin = np.linalg.solve(Xd_tr.T @ Xd_tr + pen + 1e-10 * np.eye(Xd_tr.shape[1]), Xd_tr.T @ y[train])
            p_lin[test] = Xd_te @ beta_lin

            beta_log = np.linalg.solve(Xd_tr.T @ Xd_tr + pen + 1e-10 * np.eye(Xd_tr.shape[1]), Xd_tr.T @ log_y[train])
            z_tr = Xd_tr @ beta_log
            z_te = Xd_te @ beta_log
            smear = float(np.mean(np.exp(log_y[train] - z_tr)))
            z_pred_oof[test] = z_te
            p_log_naive[test] = np.exp(np.clip(z_te, -30.0, 30.0))
            p_log_duan[test] = smear * np.exp(np.clip(z_te, -30.0, 30.0))

            # Select Ridge penalty for Poisson QMLE via inner LOKO MAE
            best_plam, best_ploss = 0.1, np.inf
            for plam in [0.01, 0.1, 1.0, 10.0]:
                errs = []
                for _, fit, val in region_splits(groups, train):
                    sc_i = fit_standardizer(X[fit])
                    p_v = fit_predict_poisson_qmle(
                        apply_standardizer(X[fit], *sc_i), y[fit],
                        apply_standardizer(X[val], *sc_i), reg_lambda=plam,
                    )
                    errs.extend(np.abs(y[val] - p_v))
                loss = float(np.mean(errs))
                if loss < best_ploss:
                    best_ploss, best_plam = loss, plam
            p_pois[test] = fit_predict_poisson_qmle(xt, y[train], xv, reg_lambda=best_plam)

            # GWR linear & log (inner LOKO selection)
            best_lin_cfg, best_lin_loss = (40.0, 1.0), np.inf
            best_log_cfg, best_log_loss = (40.0, 1.0), np.inf
            for bw in [10.0, 20.0, 40.0, 80.0]:
                for lam in [0.01, 0.1, 1.0, 10.0]:
                    e_lin, e_log = [], []
                    for _, fit, val in region_splits(groups, train):
                        sc_i = fit_standardizer(X[fit])
                        xf_i, xv_i = apply_standardizer(X[fit], *sc_i), apply_standardizer(X[val], *sc_i)
                        pr_l = RidgeGWR(bandwidth=bw, kernel='gaussian', adaptive=False, reg_lambda=lam).fit(
                            xf_i, y[fit], coords[fit]
                        ).predict(xv_i, coords[val])
                        e_lin.extend(np.abs(y[val] - pr_l))
                        z_v = RidgeGWR(bandwidth=bw, kernel='gaussian', adaptive=False, reg_lambda=lam).fit(
                            xf_i, log_y[fit], coords[fit]
                        ).predict(xv_i, coords[val])
                        e_log.extend(np.abs(y[val] - np.exp(np.clip(z_v, -30.0, 30.0))))
                    if float(np.mean(e_lin)) < best_lin_loss:
                        best_lin_loss, best_lin_cfg = float(np.mean(e_lin)), (bw, lam)
                    if float(np.mean(e_log)) < best_log_loss:
                        best_log_loss, best_log_cfg = float(np.mean(e_log)), (bw, lam)

            gwr_lin[test] = RidgeGWR(bandwidth=best_lin_cfg[0], reg_lambda=best_lin_cfg[1]).fit(
                xt, y[train], coords[train]
            ).predict(xv, coords[test])

            g_log_m = RidgeGWR(bandwidth=best_log_cfg[0], reg_lambda=best_log_cfg[1]).fit(
                xt, log_y[train], coords[train]
            )
            gz_tr = g_log_m.predict(xt, coords[train])
            gz_te = g_log_m.predict(xv, coords[test])
            g_smear = float(np.mean(np.exp(log_y[train] - gz_tr)))
            gwr_z_oof[test] = gz_te
            gwr_log_naive[test] = np.exp(np.clip(gz_te, -30.0, 30.0))
            gwr_log_duan[test] = g_smear * np.exp(np.clip(gz_te, -30.0, 30.0))

            w_te = _gaussian_weights(coords[test], coords[train], bw=best_lin_cfg[0], adaptive=False)
            gwr_pois[test] = fit_predict_poisson_qmle(
                xt, y[train], xv, weights_matrix=w_te, reg_lambda=max(best_lin_cfg[1], 0.1)
            )

        candidates = [
            ('Regresi Global', 'Linear tanpa kendala', p_lin, None),
            ('Regresi Global', 'Linear + potong nol max(0, ŷ)', np.maximum(0.0, p_lin), None),
            ('Regresi Global', 'Log-target naif exp(ẑ)', p_log_naive, z_pred_oof),
            ('Regresi Global', 'Log-target + Duan smearing latih', p_log_duan, z_pred_oof),
            ('Regresi Global', 'Quasi-Poisson GLM (log-link, y>0)', p_pois, np.log(np.maximum(p_pois, 1.0))),
            ('GWR Fixed + Ridge', 'Linear tanpa kendala', gwr_lin, None),
            ('GWR Fixed + Ridge', 'Linear + potong nol max(0, ŷ)', np.maximum(0.0, gwr_lin), None),
            ('GWR Fixed + Ridge', 'Log-target naif exp(ẑ)', gwr_log_naive, gwr_z_oof),
            ('GWR Fixed + Ridge', 'Log-target + Duan smearing latih', gwr_log_duan, gwr_z_oof),
            ('GWR Fixed + Ridge', 'Spatially Weighted Poisson QMLE (y>0)', gwr_pois, np.log(np.maximum(gwr_pois, 1.0))),
        ]
        for m_fam, scheme, pred_rp, pred_ln in candidates:
            m127 = metrics(y, pred_rp)
            m122 = metrics(y[~solo], pred_rp[~solo])
            mae_ln = float(np.mean(np.abs(log_y - pred_ln))) if pred_ln is not None else float('nan')
            rmse_ln = float(np.sqrt(np.mean((log_y - pred_ln) ** 2))) if pred_ln is not None else float('nan')
            rows.append({
                'fitur': feat_tag,
                'keluarga_model': m_fam,
                'perlakuan_target': scheme,
                'MAE_127_Rp': m127[0],
                'RMSE_127_Rp': m127[1],
                'R2_127': m127[2],
                'MAE_122_Rp': m122[0],
                'RMSE_122_Rp': m122[1],
                'MAE_skala_ln': mae_ln,
                'RMSE_skala_ln': rmse_ln,
                'prediksi_negatif': int(np.sum(pred_rp < 0)),
            })
    return rows


def audit_negative_predictions(base_preds: pd.DataFrame, sens_preds: pd.DataFrame) -> list[dict]:
    """Rangkum proporsi, magnitudo, dan wilayah terdampak prediksi negatif."""
    rows = []
    configs = [
        ('2 fitur utama (Bagian 4)', base_preds, ['Linear', 'KNN', 'Decision Tree', 'GWR']),
        ('4 fitur VIF linear (Bagian 6.7)', sens_preds,
         ['OLS', 'KNN (k=5)', 'Decision Tree (d=4)', 'GWR Fixed Gauss + Ridge',
          'GWR Adap Gauss + Ridge', 'GWR Adap Bisq + Ridge']),
    ]
    for spec_label, df, models in configs:
        for m in models:
            vals = df[m].to_numpy(dtype=float)
            neg_mask = vals < 0
            cnt = int(np.sum(neg_mask))
            if cnt == 0:
                rows.append({
                    'spesifikasi': spec_label, 'model': m, 'jumlah_negatif': 0,
                    'persen_negatif': 0.0, 'min_prediksi_Rp': float(np.min(vals)),
                    'median_negatif_Rp': 0.0, 'rerata_aktual_terdampak_Rp': 0.0,
                    'wilayah_terdampak': 'Tidak ada', 'contoh_kecamatan_ekstrem': 'Tidak ada',
                })
                continue
            sub = df.loc[neg_mask].copy()
            sub['pred'] = vals[neg_mask]
            sub = sub.sort_values('pred')
            kab_counts = sub['kab_kota'].value_counts()
            kab_str = '; '.join(f"{k.replace('Kabupaten ', '')} ({v})" for k, v in kab_counts.items())
            worst3 = '; '.join(
                f"{r.kecamatan} (-Rp{abs(float(r.pred)):,.0f})".replace(',', '.')
                for r in sub.head(3).itertuples()
            )
            rows.append({
                'spesifikasi': spec_label,
                'model': m,
                'jumlah_negatif': cnt,
                'persen_negatif': 100.0 * cnt / len(df),
                'min_prediksi_Rp': float(np.min(vals[neg_mask])),
                'median_negatif_Rp': float(np.median(vals[neg_mask])),
                'rerata_aktual_terdampak_Rp': float(sub[TARGET].mean()),
                'wilayah_terdampak': kab_str,
                'contoh_kecamatan_ekstrem': worst3,
            })
    return rows


def vif_gate_and_fair_benchmark(frame: pd.DataFrame) -> tuple[list[dict], list[dict]]:
    """Gerbang pra-pemodelan VIF dalam-lipatan, local condition number, dan benchmark 4 model yang setara."""
    groups = frame['kab_kota'].to_numpy()
    y = frame[TARGET].to_numpy(dtype=float)
    coords = frame[['lat', 'lon']].to_numpy(dtype=float)
    solo = groups == SURAKARTA

    def _screen_vif_train(sub_df: pd.DataFrame, cols: list[str], threshold: float = 5.0) -> list[str]:
        active = list(cols)
        while len(active) > 1:
            vifs = compute_vif(sub_df, active)
            worst_col = max(vifs, key=vifs.get)
            if vifs[worst_col] <= threshold:
                break
            active.remove(worst_col)
        return active

    # 1. Collinearity & local condition number diagnostics (Wheeler, 2007)
    cond_rows = []
    for tag, cols, bw, adaptive, lam in [
        ('2 fitur utama — GWR Fixed (bw=40km, λ=0)', FEATURES, 40.0, False, 0.0),
        ('7 fitur pendukung — GWR Fixed (bw=15km, λ=0)', ALL7, 15.0, False, 0.0),
        ('7 fitur pendukung — GWR Fixed (bw=15km, λ=0,001)', ALL7, 15.0, False, 1e-3),
        ('7 fitur pendukung — GWR Fixed + Ridge (bw=40km, λ=1)', ALL7, 40.0, False, 1.0),
        ('4 fitur Gate VIF≤5 — GWR Fixed (bw=40km, λ=0)', VIF4, 40.0, False, 0.0),
        ('4 fitur Gate VIF≤5 — GWR Fixed + Ridge (bw=40km, λ=1)', VIF4, 40.0, False, 1.0),
        ('4 fitur Gate VIF≤5 — GWR Adap Gauss + Ridge (25nn, λ=1)', VIF4, 25.0, True, 1.0),
    ]:
        X = frame[cols].to_numpy(dtype=float)
        vifs_global = compute_vif(frame, cols)
        max_vif_global = max(vifs_global.values())
        max_vif_folds = []
        kappas = []
        for _, train, test in region_splits(groups):
            max_vif_folds.append(max(compute_vif(frame.iloc[train], cols).values()))
            sc = fit_standardizer(X[train])
            xt = apply_standardizer(X[train], *sc)
            Xd_tr = np.column_stack([np.ones(len(xt)), xt])
            w_mat = _gaussian_weights(coords[test], coords[train], bw=bw, adaptive=adaptive)
            pen = np.eye(Xd_tr.shape[1]) * lam
            pen[0, 0] = 0.0
            for i in range(len(test)):
                w_norm = w_mat[i] / np.sum(w_mat[i])
                gram = (Xd_tr.T * w_norm) @ Xd_tr + pen
                kappas.append(float(np.linalg.cond(gram)))
        kappas_arr = np.asarray(kappas)
        cond_rows.append({
            'spesifikasi': tag,
            'jumlah_fitur': len(cols),
            'VIF_maks_global': max_vif_global,
            'VIF_maks_latih_tertinggi': float(max(max_vif_folds)),
            'kappa_lokal_median': float(np.median(kappas_arr)),
            'kappa_lokal_p90': float(np.quantile(kappas_arr, 0.90)),
            'kappa_lokal_maks': float(np.max(kappas_arr)),
            'n_lokasi_kappa_gt_30': int(np.sum(kappas_arr > 30.0)),
        })

    # Verify nested VIF screening stability across all 7 outer training folds
    nested_screened_sets = []
    for _, train, _ in region_splits(groups):
        nested_screened_sets.append(tuple(_screen_vif_train(frame.iloc[train], ALL7, threshold=5.0)))

    # 2. Fair Harmonized Benchmark (identical inner-CV MAE selection, symmetric tuning grids)
    fair_models = [
        ('Ridge Global (λ disetel)', 'ridge_global', [(0.0, lam) for lam in RIDGE_LAMBDAS]),
        ('KNN (k disetel)', 'knn', [(float(k), 0.0) for k in [3, 5, 7, 15]]),
        ('Decision Tree (d disetel)', 'tree', [(float(d), 0.0) for d in [2, 4, 6]]),
        ('GWR Fixed Gauss + Ridge', 'gwr_fixed', [(float(bw), lam) for bw in FIXED_BWS for lam in RIDGE_LAMBDAS]),
        ('GWR Adap Gauss + Ridge', 'gwr_adap', [(float(bw), lam) for bw in ADAP_GAUSS_BWS for lam in RIDGE_LAMBDAS]),
    ]

    def _run_single_fair(kind: str, X_tr: np.ndarray, y_tr: np.ndarray, c_tr: np.ndarray,
                         X_te: np.ndarray, c_te: np.ndarray, p1: float, p2: float, clip_zero: bool) -> np.ndarray:
        sc = fit_standardizer(X_tr)
        xt, xv = apply_standardizer(X_tr, *sc), apply_standardizer(X_te, *sc)
        if kind == 'ridge_global':
            Xd_tr = np.column_stack([np.ones(len(xt)), xt])
            Xd_te = np.column_stack([np.ones(len(xv)), xv])
            pen = np.eye(Xd_tr.shape[1]) * p2
            pen[0, 0] = 0.0
            beta = np.linalg.solve(Xd_tr.T @ Xd_tr + pen + 1e-10 * np.eye(Xd_tr.shape[1]), Xd_tr.T @ y_tr)
            out = Xd_te @ beta
        elif kind == 'knn':
            out = KNNRegressorScratch(k=int(round(p1))).fit(xt, y_tr).predict(xv)
        elif kind == 'tree':
            out = DecisionTreeRegressor(max_depth=int(round(p1)), min_samples_leaf=3, random_state=SEED).fit(xt, y_tr).predict(xv)
        elif kind == 'gwr_fixed':
            out = RidgeGWR(bandwidth=p1, kernel='gaussian', adaptive=False, reg_lambda=p2).fit(xt, y_tr, c_tr).predict(xv, c_te)
        elif kind == 'gwr_adap':
            out = RidgeGWR(bandwidth=p1, kernel='gaussian', adaptive=True, reg_lambda=p2).fit(xt, y_tr, c_tr).predict(xv, c_te)
        else:
            raise ValueError(kind)
        return np.maximum(0.0, out) if clip_zero else out

    fair_rows = []
    for scenario_label, mode, clip_zero in [
        ('2 fitur utama (linear setara)', 'fixed_2', False),
        ('Gate buta VIF≤5 dalam-lipatan (linear setara)', 'nested_vif', False),
        ('4 fitur non-kolinear VIF≤2,05 (linear setara)', 'fixed_vif4', False),
        ('4 fitur non-kolinear VIF≤2,05 (nonnegatif ≥0 setara)', 'fixed_vif4', True),
    ]:
        for m_label, kind, grid in fair_models:
            oof = np.empty(len(y), dtype=float)
            for _, train, test in region_splits(groups):
                if mode == 'fixed_2':
                    cols_fold = FEATURES
                elif mode == 'fixed_vif4':
                    cols_fold = VIF4
                else:
                    cols_fold = _screen_vif_train(frame.iloc[train], ALL7, threshold=5.0)
                Xf = frame[cols_fold].to_numpy(dtype=float)
                best_cfg, best_loss = grid[0], np.inf
                for p1, p2 in grid:
                    errs = []
                    for _, fit, val in region_splits(groups, train):
                        pr = _run_single_fair(kind, Xf[fit], y[fit], coords[fit], Xf[val], coords[val], p1, p2, clip_zero)
                        errs.extend(np.abs(y[val] - pr))
                    loss = float(np.mean(errs))
                    if loss < best_loss:
                        best_loss, best_cfg = loss, (p1, p2)
                oof[test] = _run_single_fair(
                    kind, Xf[train], y[train], coords[train], Xf[test], coords[test], best_cfg[0], best_cfg[1], clip_zero
                )
            m127 = metrics(y, oof)
            m122 = metrics(y[~solo], oof[~solo])
            fair_rows.append({
                'skenario': scenario_label,
                'model': m_label,
                'kandidat_grid': len(grid),
                'MAE_127': m127[0],
                'RMSE_127': m127[1],
                'R2_127': m127[2],
                'MAE_122_tanpa_solo': m122[0],
                'RMSE_122_tanpa_solo': m122[1],
                'MAE_surakarta': float(np.mean(np.abs(y[solo] - oof[solo]))),
                'prediksi_negatif': int(np.sum(oof < 0)),
                'fitur_konsisten_7_lipatan': (
                    str(len(set(nested_screened_sets)) == 1) if mode == 'nested_vif'
                    else ('Terkunci (4)' if mode == 'fixed_vif4' else 'Terkunci (2)')
                ),
            })
    return cond_rows, fair_rows


def evaluate_point_sensitivity(frame: pd.DataFrame,
                               polys: dict[tuple[str, str], list[list[list[float]]]]) -> list[dict]:
    """Uji sensitivitas GWR terhadap 4 representasi titik lokasi kecamatan pada 127 poligon."""
    audit_coords = pd.read_csv(DATA / 'processed/audit_koordinat_127.csv').set_index(KEY)
    colab_coords = pd.read_csv(DATA / 'sumber/koordinat_solo_raya.csv').set_index(KEY)

    keys = list(frame[KEY].itertuples(index=False, name=None))
    pos_coords = frame[['lat', 'lon']].to_numpy(dtype=float)

    cent_coords = np.array([_polygon_centroid_wgs84(polys[k]) for k in keys], dtype=float)
    hdx_coords = np.empty_like(pos_coords)
    nb_coords = np.empty_like(pos_coords)
    for idx, k in enumerate(keys):
        row_a = audit_coords.loc[k]
        if pd.notna(row_a['lat_hdx_bps']) and pd.notna(row_a['lon_hdx_bps']):
            hdx_coords[idx] = [float(row_a['lat_hdx_bps']), float(row_a['lon_hdx_bps'])]
        else:
            hdx_coords[idx] = pos_coords[idx]
        row_c = colab_coords.loc[k]
        nb_coords[idx] = [float(row_c['lat']), float(row_c['lon'])]

    # Baseline non-spatial reference MAEs for ranking check
    base_2f = pd.read_csv(ROOT / 'artifacts/spasial/metrik.csv').set_index('model')
    nonspatial_2f = {m: float(base_2f.loc[m, 'MAE_Rp_m2']) for m in ['Linear', 'KNN', 'Decision Tree']}
    sens_4f = pd.read_csv(ROOT / 'artifacts/sensitivitas_gwr/ringkasan_loro.csv')
    sens_4f_sub = sens_4f[(sens_4f['fitur'] == '4_fitur_vif') & (sens_4f['target'] == 'linear')].set_index('model')
    nonspatial_4f = {m: float(sens_4f_sub.loc[m, 'MAE_127']) for m in ['OLS', 'KNN (k=5)', 'Decision Tree (d=4)']}

    groups = frame['kab_kota'].to_numpy()
    y = frame[TARGET].to_numpy(dtype=float)
    X2 = frame[FEATURES].to_numpy(dtype=float)
    X4 = frame[VIF4].to_numpy(dtype=float)

    point_sets = [
        ('BIG ST_PointOnSurface (acuan)', pos_coords),
        ('BIG Centroid Geometris Poligon', cent_coords),
        ('BPS/HDX Center Point (124+3 BIG)', hdx_coords),
        ('Centroid GADM 4.1 / Notebook', nb_coords),
    ]
    rows = []
    for label, c_arr in point_sets:
        shift_m = np.diag(haversine_km(pos_coords[:, 0], pos_coords[:, 1], c_arr[:, 0], c_arr[:, 1])) * 1000.0
        # 1. Locked 2-feature GWR protocol (bw in [5, 10, 20, 40], MAE inner selection, lambda=0)
        oof_2f = np.empty(len(y))
        for _, train, test in region_splits(groups):
            best_bw, best_loss = 40.0, np.inf
            for bw in [5.0, 10.0, 20.0, 40.0]:
                errs = []
                for _, fit, val in region_splits(groups, train):
                    sc_i = fit_standardizer(X2[fit])
                    pr = RidgeGWR(bandwidth=bw, kernel='gaussian', adaptive=False, reg_lambda=0.0).fit(
                        apply_standardizer(X2[fit], *sc_i), y[fit], c_arr[fit]
                    ).predict(apply_standardizer(X2[val], *sc_i), c_arr[val])
                    errs.extend(np.abs(y[val] - pr))
                loss = float(np.mean(errs))
                if loss < best_loss:
                    best_loss, best_bw = loss, bw
            sc = fit_standardizer(X2[train])
            oof_2f[test] = RidgeGWR(bandwidth=best_bw, kernel='gaussian', adaptive=False, reg_lambda=0.0).fit(
                apply_standardizer(X2[train], *sc), y[train], c_arr[train]
            ).predict(apply_standardizer(X2[test], *sc), c_arr[test])
        m2 = metrics(y, oof_2f)
        rank_2f = 1 + sum(1 for v in nonspatial_2f.values() if v < m2[0])

        # 2. 4-feature VIF GWR Adaptive Gaussian + Ridge (same protocol as sensitivity.py)
        oof_4f = np.empty(len(y))
        for _, train, test in region_splits(groups):
            best_cfg, best_rmse = (40.0, 1.0), np.inf
            for bw in ADAP_GAUSS_BWS:
                for lam in RIDGE_LAMBDAS:
                    sq = []
                    for _, fit, val in region_splits(groups, train):
                        sc_i = fit_standardizer(X4[fit])
                        pr = RidgeGWR(bandwidth=bw, kernel='gaussian', adaptive=True, reg_lambda=lam).fit(
                            apply_standardizer(X4[fit], *sc_i), y[fit], c_arr[fit]
                        ).predict(apply_standardizer(X4[val], *sc_i), c_arr[val])
                        sq.extend((y[val] - pr) ** 2)
                    rmse_in = float(np.sqrt(np.mean(sq)))
                    if rmse_in < best_rmse:
                        best_rmse, best_cfg = rmse_in, (bw, lam)
            sc = fit_standardizer(X4[train])
            oof_4f[test] = RidgeGWR(bandwidth=best_cfg[0], kernel='gaussian', adaptive=True, reg_lambda=best_cfg[1]).fit(
                apply_standardizer(X4[train], *sc), y[train], c_arr[train]
            ).predict(apply_standardizer(X4[test], *sc), c_arr[test])
        m4 = metrics(y, oof_4f)
        rank_4f = 1 + sum(1 for v in nonspatial_4f.values() if v < m4[0])

        rows.append({
            'representasi_titik': label,
            'median_geser_m': float(np.median(shift_m)),
            'maks_geser_m': float(np.max(shift_m)),
            'GWR_2fitur_MAE': m2[0],
            'GWR_2fitur_RMSE': m2[1],
            'peringkat_GWR_2fitur': f'{rank_2f}/4',
            'GWR_4fitur_Adap_MAE': m4[0],
            'GWR_4fitur_Adap_RMSE': m4[1],
            'peringkat_GWR_4fitur': f'{rank_4f}/4',
        })
    return rows


def render_residual_lisa_figure(output: Path, keys: list[tuple[str, str]],
                                base_preds: pd.DataFrame, sens_preds: pd.DataFrame,
                                moran_results: dict[str, dict]) -> None:
    """Buat figur 2x2 peta residual out-of-fold dan klaster LISA signifikan pada 127 kecamatan."""
    disp = json.loads((DATA / 'processed/solo_raya_display.geojson').read_text(encoding='utf-8'))
    geom_by_key = {(f['properties']['kab_kota'], f['properties']['kecamatan']): f['geometry']
                   for f in disp['features']}

    y = base_preds[TARGET].to_numpy(dtype=float)
    res_gwr_2f = (y - base_preds['GWR'].to_numpy(dtype=float)) / 1e6
    res_gwr_4f = (y - sens_preds['GWR Adap Gauss + Ridge'].to_numpy(dtype=float)) / 1e6
    lisa_2f = moran_results['2fitur__GWR']['labels']
    lisa_4f = moran_results['4fitur__GWR Adap Gauss + Ridge']['labels']

    fig, axes = plt.subplots(2, 2, figsize=(11.2, 9.2), layout='constrained')
    cmap_div = plt.cm.RdBu_r
    vmax = 4.5

    def _draw_continuous(ax, values, title):
        patches, cols = [], []
        for idx, k in enumerate(keys):
            geom = geom_by_key[k]
            polys = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
            val = float(np.clip(values[idx], -vmax, vmax))
            for poly in polys:
                patches.append(MplPolygon(np.asarray(poly[0])[:, :2], closed=True))
                cols.append(val)
        pc = PatchCollection(patches, cmap=cmap_div, edgecolor='#333333', linewidth=0.25)
        pc.set_clim(-vmax, vmax)
        pc.set_array(np.asarray(cols))
        ax.add_collection(pc)
        ax.autoscale_view()
        ax.set_aspect('equal')
        ax.set_axis_off()
        ax.set_title(title, fontsize=10, fontweight='bold')
        return pc

    lisa_palette = {
        'HH': '#b2182b',
        'LL': '#2166ac',
        'HL': '#ef8a62',
        'LH': '#67a9cf',
        'NS': '#eeeeee',
    }

    def _draw_lisa(ax, labels, title):
        for idx, k in enumerate(keys):
            geom = geom_by_key[k]
            polys = [geom['coordinates']] if geom['type'] == 'Polygon' else geom['coordinates']
            face = lisa_palette[str(labels[idx])]
            for poly in polys:
                xy = np.asarray(poly[0])[:, :2]
                ax.add_patch(MplPolygon(xy, closed=True, facecolor=face, edgecolor='#444444', linewidth=0.25))
        ax.autoscale_view()
        ax.set_aspect('equal')
        ax.set_axis_off()
        ax.set_title(title, fontsize=10, fontweight='bold')

    i2 = moran_results['2fitur__GWR']
    i4 = moran_results['4fitur__GWR Adap Gauss + Ridge']
    fmt3 = lambda v: f'{v:.3f}'.replace('.', ',')
    fmt4 = lambda v: f'{v:.4f}'.replace('.', ',')
    pc1 = _draw_continuous(
        axes[0, 0], res_gwr_2f,
        f"a  Residual GWR 2 Fitur Utama (I={fmt3(i2['moran_i'])}; p={fmt4(i2['p_perm'])})"
    )
    _draw_continuous(
        axes[0, 1], res_gwr_4f,
        f"b  Residual GWR Adap+Ridge 4 Fitur VIF (I={fmt3(i4['moran_i'])}; p={fmt4(i4['p_perm'])})"
    )
    cbar = fig.colorbar(pc1, ax=[axes[0, 0], axes[0, 1]], orientation='horizontal', fraction=0.045, pad=0.02,
                        label='Residual y − ŷ (juta Rp/m², dipotong pada ±4,5 juta untuk keterbacaan)')
    cbar.set_ticks([-4, -2, 0, 2, 4])

    _draw_lisa(axes[1, 0], lisa_2f, f"c  Klaster LISA Residual GWR 2 Fitur (sig. p<0,05: {i2['n_sig_total']} kec.)")
    _draw_lisa(axes[1, 1], lisa_4f, f"d  Klaster LISA Residual GWR Adap+Ridge 4 Fitur (sig. p<0,05: {i4['n_sig_total']} kec.)")

    legend_handles = [
        Patch(facecolor='#b2182b', edgecolor='#444444', label='High-High (kantong underprediction)'),
        Patch(facecolor='#2166ac', edgecolor='#444444', label='Low-Low (kantong overprediction)'),
        Patch(facecolor='#ef8a62', edgecolor='#444444', label='High-Low (outlier tinggi)'),
        Patch(facecolor='#67a9cf', edgecolor='#444444', label='Low-High (outlier rendah)'),
        Patch(facecolor='#eeeeee', edgecolor='#444444', label='Tidak signifikan (p ≥ 0,05)'),
    ]
    fig.legend(handles=legend_handles, loc='outside lower center', ncol=3, frameon=False, fontsize=8.5)
    fig.savefig(output / 'peta_residual_lisa.png', dpi=180, bbox_inches='tight')
    plt.close(fig)


def run(output: Path = ROOT / 'artifacts/diagnostik_lanjut') -> Path:
    """Jalankan seluruh diagnostik metodologis lanjutan dan simpan keluarannya."""
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    audit = new_audit(DATA / 'koordinat.csv', {'bootstrap_reps': BOOT_REPS, 'moran_perms': MORAN_PERMS})
    audit.update(
        protocol='rigor_diagnostics_v1',
        spasial_pred_sha256=sha256(ROOT / 'artifacts/spasial/prediksi_uji.csv'),
        sens_pred_sha256=sha256(ROOT / 'artifacts/sensitivitas_gwr/prediksi_4fitur_linear.csv'),
    )
    save_audit(output, audit)

    frame = load_sensitivity_frame(DATA / 'koordinat.csv').sort_values(KEY).reset_index(drop=True)
    base_preds = pd.read_csv(ROOT / 'artifacts/spasial/prediksi_uji.csv').sort_values(KEY).reset_index(drop=True)
    sens_preds = pd.read_csv(ROOT / 'artifacts/sensitivitas_gwr/prediksi_4fitur_linear.csv').sort_values(KEY).reset_index(drop=True)
    pd.testing.assert_frame_equal(frame[KEY + [TARGET]], base_preds[KEY + [TARGET]])
    pd.testing.assert_frame_equal(frame[KEY + [TARGET]], sens_preds[KEY + [TARGET]])

    keys = list(frame[KEY].itertuples(index=False, name=None))
    y = frame[TARGET].to_numpy(dtype=float)
    groups = frame['kab_kota'].to_numpy()
    polys = _load_solo_polygons()
    adj, w = build_queen_weights(keys, polys)

    # 1. Block bootstrap CI & dual metrics
    boot_2f = block_bootstrap_summary(
        y, groups, {m: base_preds[m].to_numpy(dtype=float) for m in ['Linear', 'KNN', 'Decision Tree', 'GWR']},
        ref_model='Linear', seed=SEED,
    )
    for r in boot_2f:
        r['skenario'] = '2_fitur_utama'
    boot_4f = block_bootstrap_summary(
        y, groups,
        {m: sens_preds[m].to_numpy(dtype=float) for m in [
            'OLS', 'KNN (k=5)', 'Decision Tree (d=4)',
            'GWR Fixed Gauss + Ridge', 'GWR Adap Gauss + Ridge', 'GWR Adap Bisq + Ridge'
        ]},
        ref_model='OLS', seed=SEED,
    )
    for r in boot_4f:
        r['skenario'] = '4_fitur_vif_linear'
    pd.DataFrame(boot_2f + boot_4f).to_csv(output / 'block_bootstrap.csv', index=False)

    # 2. Area of Applicability (AoA)
    aoa_rows = []
    aoa_frames = []
    for tag, cols in [('2 fitur utama', FEATURES), ('4 fitur VIF', VIF4), ('7 fitur pendukung', ALL7)]:
        df_aoa, summ = compute_aoa_loko(frame, cols)
        df_aoa.insert(0, 'ruang_fitur', tag)
        aoa_frames.append(df_aoa)
        # Attach MAE inside vs outside AoA for representative models
        outside_m = df_aoa['di_luar_AoA'].to_numpy()
        ref_pred = base_preds['GWR'].to_numpy(dtype=float) if tag == '2 fitur utama' else sens_preds['GWR Adap Gauss + Ridge'].to_numpy(dtype=float)
        knn_pred = base_preds['KNN'].to_numpy(dtype=float) if tag == '2 fitur utama' else sens_preds['KNN (k=5)'].to_numpy(dtype=float)
        summ.update(
            ruang_fitur=tag,
            MAE_GWR_dalam_AoA=float(np.mean(np.abs(y[~outside_m] - ref_pred[~outside_m]))),
            MAE_GWR_luar_AoA=float(np.mean(np.abs(y[outside_m] - ref_pred[outside_m]))) if np.any(outside_m) else 0.0,
            MAE_KNN_dalam_AoA=float(np.mean(np.abs(y[~outside_m] - knn_pred[~outside_m]))),
            MAE_KNN_luar_AoA=float(np.mean(np.abs(y[outside_m] - knn_pred[outside_m]))) if np.any(outside_m) else 0.0,
        )
        aoa_rows.append(summ)
    pd.DataFrame(aoa_rows).to_csv(output / 'aoa_ringkasan.csv', index=False)
    pd.concat(aoa_frames, ignore_index=True).to_csv(output / 'aoa_per_kecamatan.csv', index=False)

    # 3. Moran's I & LISA residual diagnostics
    moran_rows = []
    moran_cache = {}
    moran_targets = [('Target harga aktual (2020)', 'Aktual', y, np.zeros_like(y))]
    for m in ['Linear', 'KNN', 'Decision Tree', 'GWR']:
        moran_targets.append(('2 fitur utama', m, y - base_preds[m].to_numpy(dtype=float), base_preds[m].to_numpy(dtype=float)))
    for m in ['OLS', 'KNN (k=5)', 'Decision Tree (d=4)', 'GWR Fixed Gauss + Ridge', 'GWR Adap Gauss + Ridge']:
        moran_targets.append(('4 fitur VIF linear', m, y - sens_preds[m].to_numpy(dtype=float), sens_preds[m].to_numpy(dtype=float)))

    for idx_m, (scen, mname, vec, _) in enumerate(moran_targets):
        res = moran_and_lisa(vec, w, seed=SEED + idx_m)
        cache_key = f"{'2fitur' if scen == '2 fitur utama' else '4fitur'}__{mname}"
        moran_cache[cache_key] = res
        moran_rows.append({
            'skenario': scen,
            'model': mname,
            'moran_I': res['moran_i'],
            'ekspektasi_I': res['expected_i'],
            'z_score': res['z_score'],
            'p_permutasi': res['p_perm'],
            'n_klaster_sig': res['n_sig_total'],
            'HH': res['n_HH'],
            'LL': res['n_LL'],
            'HL': res['n_HL'],
            'LH': res['n_LH'],
        })
    pd.DataFrame(moran_rows).to_csv(output / 'moran_residual.csv', index=False)
    render_residual_lisa_figure(output, keys, base_preds, sens_preds, moran_cache)

    # 4. Negative predictions & target treatment (Duan smearing + Poisson QMLE)
    pd.DataFrame(audit_negative_predictions(base_preds, sens_preds)).to_csv(
        output / 'detail_prediksi_negatif.csv', index=False
    )
    pd.DataFrame(evaluate_target_treatments(frame)).to_csv(
        output / 'retransformasi_dan_nonnegatif.csv', index=False
    )

    # 5. VIF pre-modeling gate, local condition number, & fair benchmark
    cond_rows, fair_rows = vif_gate_and_fair_benchmark(frame)
    pd.DataFrame(cond_rows).to_csv(output / 'kolinearitas_dan_kondisi.csv', index=False)
    pd.DataFrame(fair_rows).to_csv(output / 'perbandingan_setara.csv', index=False)

    # 6. Representative point sensitivity
    pd.DataFrame(evaluate_point_sensitivity(frame, polys)).to_csv(
        output / 'sensitivitas_titik.csv', index=False
    )

    audit['queen_neighbors_min'] = int(np.min(adj.sum(axis=1)))
    audit['queen_neighbors_median'] = float(np.median(adj.sum(axis=1)))
    audit['queen_neighbors_max'] = int(np.max(adj.sum(axis=1)))
    audit['status'] = 'complete'
    save_audit(output, audit)
    verify_rigor(output)
    return output


def verify_rigor(folder: Path) -> None:
    """Verifikasi kelengkapan dan konsistensi keluaran diagnostik lanjutan."""
    if not __debug__:
        raise RuntimeError('Jalankan verifikasi tanpa python -O agar assertions aktif.')
    folder = Path(folder)
    audit = json.loads((folder / 'audit.json').read_text(encoding='utf-8'))
    assert audit.get('status') == 'complete' and audit.get('protocol') == 'rigor_diagnostics_v1'
    expected_files = [
        'block_bootstrap.csv',
        'aoa_ringkasan.csv',
        'aoa_per_kecamatan.csv',
        'moran_residual.csv',
        'detail_prediksi_negatif.csv',
        'retransformasi_dan_nonnegatif.csv',
        'kolinearitas_dan_kondisi.csv',
        'perbandingan_setara.csv',
        'sensitivitas_titik.csv',
        'peta_residual_lisa.png',
    ]
    for fname in expected_files:
        p = folder / fname
        assert p.is_file() and p.stat().st_size > 0, f'Berkas diagnostik hilang/kosong: {fname}'

    boot = pd.read_csv(folder / 'block_bootstrap.csv')
    assert len(boot) == 10
    assert (boot['MAE_127_ci_lo'] <= boot['MAE_127']).all() and (boot['MAE_127'] <= boot['MAE_127_ci_hi']).all()

    aoa_all = pd.read_csv(folder / 'aoa_per_kecamatan.csv')
    assert len(aoa_all) == 127 * 3

    retrans = pd.read_csv(folder / 'retransformasi_dan_nonnegatif.csv')
    pois = retrans[retrans['perlakuan_target'].str.contains('Poisson')]
    assert (pois['prediksi_negatif'] == 0).all(), 'Poisson QMLE tidak boleh menghasilkan prediksi negatif.'
    clip = retrans[retrans['perlakuan_target'].str.contains('potong nol')]
    assert (clip['prediksi_negatif'] == 0).all()

    titik = pd.read_csv(folder / 'sensitivitas_titik.csv')
    assert len(titik) == 4
    print(f'Valid diagnostik lanjut: {folder} (10 berkas terverifikasi)')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'artifacts/diagnostik_lanjut')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        verify_rigor(args.output)
    else:
        run(args.output)


if __name__ == '__main__':
    main()
