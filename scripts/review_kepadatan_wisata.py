"""Uji lintas wilayah untuk gradien harga perkotaan dan konsentrasi wisata dataran tinggi."""
import argparse
import json
import numpy as np
from scipy.stats import rankdata

from eksperimen_akses_medan import ROOT, TARGET, by_key, read, save, split, metrics
from tanah.colab_models import haversine_km


def main(out):
    base = by_key(ROOT / 'data/processed/variabel_pendukung_2020.csv')
    terrain = by_key(ROOT / 'data/processed/akses_medan/fitur.csv')
    coords = by_key(ROOT / 'data/koordinat.csv')
    assert base.keys() == terrain.keys() == coords.keys()
    keys = list(base)
    groups = np.array([key[0] for key in keys])
    y = np.array([float(base[k][TARGET]) for k in keys])
    lat, lon = np.array([[float(coords[k][a]) for a in ('lat', 'lon')] for k in keys]).T
    geo = haversine_km(lat, lon, lat, lon)
    pois = [p for p in read(ROOT / 'data/processed/akses_medan/poi_osm.csv') if p['kelompok'] == 'wisata']
    nearby = (haversine_km(lat, lon, [float(p['lat']) for p in pois],
                           [float(p['lon']) for p in pois]) <= 5).sum(axis=1)
    density = np.array([float(base[k]['kepadatan_penduduk_proksi']) for k in keys])
    built = [float(base[k]['built_pct']) for k in keys]
    elevation = np.array([float(terrain[k]['elevasi_median_m']) for k in keys])
    slope = [float(terrain[k]['lereng_median_derajat']) for k in keys]
    distance = [[float(terrain[k][col]) for k in keys] for col in ('jarak_wisata_km', 'jarak_kampus_km')]
    features = dict(kepadatan_penduduk_proksi=density, built_pct=built, objek_wisata_5km=nearby,
                    elevasi_median_m=elevation, lereng_median_derajat=slope,
                    jarak_wisata_km=distance[0], jarak_kampus_km=distance[1])
    out.mkdir(parents=True, exist_ok=True)
    dataset = [dict(tahun=2020, kab_kota=k[0], kecamatan=k[1],
                    **{col: float(values[i]) for col, values in features.items()}, **{TARGET: y[i]})
               for i, k in enumerate(keys)]
    save(out / 'dataset.csv', dataset)
    # Conditional permutation test on within-region centered ranks.
    ranks_y = rankdata(y)
    rng = np.random.default_rng(2020)
    indices = [np.flatnonzero(groups == name) for name in np.unique(groups)]
    permutations = np.tile(np.arange(len(y)), (9999, 1))
    for block in indices:
        permutations[:, block] = rng.permuted(permutations[:, block], axis=1)
    correlations = []
    for col, values in features.items():
        rx, ry = rankdata(values), ranks_y.copy()
        pooled_rho = np.corrcoef(rx, ry)[0, 1]
        for block in indices:
            rx[block] -= rx[block].mean()
            ry[block] -= ry[block].mean()
        denom = np.linalg.norm(rx) * np.linalg.norm(ry)
        within = rx @ ry / denom
        permuted = ry[permutations] @ rx / denom
        p = (1 + np.count_nonzero(np.abs(permuted) >= abs(within) - 1e-12)) / (len(permutations)+1)
        correlations.append(dict(variabel=col, n=len(y), pearson=np.corrcoef(values, y)[0,1],
                                 spearman=pooled_rho, rho_dalam_blok=within, p_permutasi=p,
                                 p_bonferroni=min(1., p * len(features))))
    save(out / 'korelasi.csv', correlations)
    tourism = np.log1p(nearby)
    specs = {'kepadatan': [density], 'kota': [density, built],
             'kota_wisata_medan': [density, built, tourism, elevation, slope],
             'interaksi': [density, built, tourism, elevation, slope, tourism * elevation]}
    specs['akses_lengkap'] = specs['kota_wisata_medan'] + distance
    rows, scores, folds = [], [], []
    winners = {}
    for spec, columns in specs.items():
        x = np.column_stack(columns)
        for model, widths in [('Ridge', [None]), ('GWR ridge', [15, 40, 80])]:
            def estimate(train, test, width, penalty):
                center, scale = x[train].mean(axis=0), x[train].std(axis=0)
                scale[scale == 0] = 1
                z = (x - center) / scale
                w = np.ones((len(test), len(train))) if width is None else np.exp(-.5*(geo[np.ix_(test, train)]/width)**2)
                w /= w.sum(axis=1, keepdims=True)
                mx, my = w @ z[train], w @ y[train]
                xc = z[train] - mx[:, None, :]
                xtw = xc.transpose(0, 2, 1) * w[:, None, :]
                coef = np.linalg.solve(xtw @ xc + penalty*np.eye(x.shape[1]),
                                       xtw @ (y[train]-my[:, None])[:, :, None])
                return np.maximum(0, my + np.sum((z[test]-mx)*coef[:, :, 0], axis=1))

            pred = np.full(len(y), np.nan)
            for region, train, test in split(groups, np.arange(len(y))):
                candidates = [(h, a) for h in widths for a in (.01, .1, 1.)]
                validation = []
                for h, a in candidates:
                    errors = np.concatenate([y[val]-estimate(fit, val, h, a) for _, fit, val in split(groups, train)])
                    mae = np.abs(errors).mean()
                    rmse = np.sqrt(np.square(errors).mean())
                    validation.append(mae)
                    if region not in winners or rmse < winners[region]['rmse_internal']:
                        winners[region] = dict(model=model, spesifikasi=spec, bandwidth_km=h, penalti=a,
                                               rmse_internal=rmse, test=test, pred=estimate(train, test, h, a))
                width, penalty = candidates[np.argmin(validation)]
                pred[test] = estimate(train, test, width, penalty)
                folds.append(dict(model=model, spesifikasi=spec, wilayah=region, bandwidth_km=width,
                                  penalti=penalty, **metrics(y[test], pred[test])))
            assert np.isfinite(pred).all()
            scores.append(dict(model=model, spesifikasi=spec, **metrics(y, pred)))
            for i, (region, district) in enumerate(keys):
                rows.append(dict(model=model, spesifikasi=spec, kab_kota=region, kecamatan=district,
                                 kepadatan=density[i], objek_wisata_5km=nearby[i], elevasi=elevation[i],
                                 lereng=slope[i], aktual=y[i], prediksi=pred[i], selisih=pred[i]-y[i]))
    out.mkdir(parents=True, exist_ok=True)
    oof = np.full(len(y), np.nan)
    selected = []
    for region, winner in winners.items():
        test, pred = winner.pop('test'), winner.pop('pred')
        oof[test] = pred
        selected.append(dict(wilayah=region, **winner, n=len(test), **metrics(y[test],pred)))
        for i, value in zip(test, pred):
            dataset[i].update(prediksi_seleksi=float(value), galat_seleksi=float(abs(value-y[i])),
                              model_terpilih=winner['model'], fitur_terpilih=winner['spesifikasi'])
    if len(winners) != 7 or not np.isfinite(oof).all():
        raise ValueError('Prediksi luar tidak lengkap')
    fixed = {(r['kab_kota'], r['kecamatan']): r for r in rows
             if r['model'] == 'Ridge' and r['spesifikasi'] == 'kota_wisata_medan'}
    for row in dataset:
        reference = fixed[row['kab_kota'], row['kecamatan']]
        row.update(prediksi_ridge=reference['prediksi'], galat_ridge=abs(reference['selisih']))
    scores.append(dict(model='Seleksi RMSE', spesifikasi='validasi internal', **metrics(y,oof)))
    save(out / 'pilihan_per_wilayah.csv', selected)
    save(out / 'prediksi_seleksi.csv', dataset)
    (out / 'review.json').write_text(json.dumps(dataset, ensure_ascii=False, allow_nan=False))
    for name, values in [('metrik',scores), ('per_wilayah',folds), ('prediksi_uji',rows)]:
        save(out / (name + '.csv'), values)


if __name__ == '__main__':
    from pathlib import Path
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'hasil/review_kepadatan_wisata')
    main(parser.parse_args().output)
