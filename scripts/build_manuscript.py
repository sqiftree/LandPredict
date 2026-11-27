"""Build the empirical manuscript from verified outputs, then render its DOCX."""
import csv
import json
import math
import statistics
import sys
from collections import defaultdict
from pathlib import Path

from render_docx import render
from audit_dataset import main as audit_dataset

ROOT = Path(__file__).resolve().parents[1]
MODELS = ['Linear', 'KNN', 'Decision Tree', 'GWR']


def read_csv(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream))


def table(headers, rows):
    return '\n'.join(['| ' + ' | '.join(map(str, headers)) + ' |',
                      '| ' + ' | '.join(['---'] * len(headers)) + ' |',
                      *['| ' + ' | '.join(map(str, row)) + ' |' for row in rows]])


def rupiah(value):
    return f'{float(value):,.0f}'.replace(',', '.')


def signed_rupiah(value):
    val = float(value)
    if abs(val) < 0.5:
        return '0'
    sign = '+' if val > 0 else '−'
    return f'{sign}{abs(val):,.0f}'.replace(',', '.')


def decimal_id(value, digits=2):
    return f'{float(value):,.{digits}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def quantile(sorted_values, q):
    pos = q * (len(sorted_values) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(sorted_values) - 1)
    frac = pos - lo
    return sorted_values[lo] * (1 - frac) + sorted_values[hi] * frac


def describe_column(rows, col):
    vals = sorted(float(r[col]) for r in rows)
    return {
        'min': vals[0],
        'q1': quantile(vals, 0.25),
        'median': quantile(vals, 0.50),
        'q3': quantile(vals, 0.75),
        'mean': sum(vals) / len(vals),
        'max': vals[-1],
        'std': statistics.stdev(vals),
    }


def verify_stdlib(folder, colab=False):
    """Fallback verifier using only stdlib when numpy/pandas are absent."""
    if not __debug__:
        raise RuntimeError('Jalankan verifikasi tanpa python -O agar assertions aktif.')
    audit_path = folder / 'audit.json'
    if not audit_path.is_file():
        raise FileNotFoundError('audit.json wajib tersedia untuk memverifikasi keluaran eksperimen.')
    audit = json.loads(audit_path.read_text(encoding='utf-8'))
    if audit is not None:
        assert audit['status'] == 'complete', 'Eksperimen gagal/belum selesai; CSV lama tidak boleh dipakai.'
    source = read_csv(ROOT / 'data/harga_tanah_2020.csv')
    predictions = read_csv(folder / 'prediksi_uji.csv')
    metrics = read_csv(folder / 'metrik.csv')
    folds = read_csv(folder / 'per_wilayah.csv')
    assert len(source) == len(predictions) == 127, 'Harus ada 127 kecamatan'
    src_by_key = {(r['kab_kota'], r['kecamatan']): r for r in source}
    pred_by_key = {(r['kab_kota'], r['kecamatan']): r for r in predictions}
    assert len(src_by_key) == 127 and len(pred_by_key) == 127
    assert set(src_by_key) == set(pred_by_key)
    for key, src_row in src_by_key.items():
        pred_row = pred_by_key[key]
        for col, val in src_row.items():
            assert pred_row[col] == val, f'Ketidakcocokan sumber pada {key}: {col}'
    regions = {r['kab_kota'] for r in predictions}
    assert len(regions) == 7
    assert len(metrics) == len(MODELS) and {r['model'] for r in metrics} == set(MODELS)
    assert len(folds) == 7 * len(MODELS) and {r['model'] for r in folds} == set(MODELS)
    assert len({(r['model'], r['wilayah_uji']) for r in folds}) == 7 * len(MODELS)
    metrics_by_model = {r['model']: r for r in metrics}
    expected = {'Linear': 739020, 'KNN': 732073, 'Decision Tree': 756462}
    target_mean = sum(float(r['harga_tanah_rata_rata_rp_m2']) for r in predictions) / len(predictions)
    ss_tot = sum((float(r['harga_tanah_rata_rata_rp_m2']) - target_mean) ** 2 for r in predictions)
    by_region = defaultdict(list)
    for r in predictions:
        by_region[r['kab_kota']].append(r)
    for model in MODELS:
        preds = [float(r[model]) for r in predictions]
        assert all(math.isfinite(v) for v in preds), f'Prediksi tidak valid: {model}'
        errors = [float(r['harga_tanah_rata_rata_rp_m2']) - float(r[model]) for r in predictions]
        mae = sum(abs(e) for e in errors) / len(errors)
        rmse = math.sqrt(sum(e ** 2 for e in errors) / len(errors))
        r2 = 1.0 - sum(e ** 2 for e in errors) / ss_tot
        row = metrics_by_model[model]
        assert math.isclose(mae, float(row['MAE_Rp_m2']), rel_tol=1e-10)
        assert math.isclose(rmse, float(row['RMSE_Rp_m2']), rel_tol=1e-10)
        assert math.isclose(r2, float(row['R2']), rel_tol=1e-10)
        if colab:
            assert audit["protocol"] == "colab_log7"
        elif model in expected:
            assert round(mae) == expected[model], f'MAE baseline berubah: {model}: {mae}'
        block = {r['wilayah_uji']: r for r in folds if r['model'] == model}
        assert set(block) == regions
        for region, group in by_region.items():
            assert int(block[region]['n']) == len(group)
            reg_errs = [float(r['harga_tanah_rata_rata_rp_m2']) - float(r[model]) for r in group]
            reg_mae = sum(abs(e) for e in reg_errs) / len(reg_errs)
            assert math.isclose(float(block[region]['MAE_Rp_m2']), reg_mae, rel_tol=1e-10)
            if 'RMSE_Rp_m2' in block[region]:
                reg_rmse = math.sqrt(sum(e ** 2 for e in reg_errs) / len(reg_errs))
                assert math.isclose(float(block[region]['RMSE_Rp_m2']), reg_rmse, rel_tol=1e-10)
        if audit is not None:
            entries = [e for e in audit['outer_folds'] if e['model'] == model]
            assert len(entries) == 7
            assert {e['test_region'] for e in entries} == regions
            for entry in entries:
                held_out = entry['test_region']
                assert set(entry['train_regions']) == regions - {held_out}
                assert {tuple(k) for k in entry['test_keys']} == {(r['kab_kota'], r['kecamatan']) for r in by_region[held_out]}


def prefer_hasil(hasil_rel, artifact_rel):
    """Use local hasil/ output when present, falling back to committed artifacts/."""
    candidate = ROOT / hasil_rel
    return candidate if candidate.exists() else ROOT / artifact_rel


def _preds_val_eq(a, b):
    return math.isclose(float(a), float(b), rel_tol=0.0, abs_tol=1e-9)


def verify_sensitivity_stdlib(folder):
    """Verify GWR sensitivity CSVs and audit.json using stdlib only."""
    if not __debug__:
        raise RuntimeError('Jalankan verifikasi tanpa python -O agar assertions aktif.')
    audit = json.loads((folder / 'audit.json').read_text(encoding='utf-8'))
    assert audit.get('status') == 'complete', 'Analisis sensitivitas GWR belum selesai.'
    assert audit.get('protocol') == 'gwr_sensitivity_v1'

    source = read_csv(ROOT / 'data/harga_tanah_2020.csv')
    preds = read_csv(folder / 'prediksi_4fitur_linear.csv')
    ringkasan = read_csv(folder / 'ringkasan_loro.csv')
    per_wilayah = read_csv(folder / 'per_wilayah_4fitur_linear.csv')
    enam = read_csv(folder / 'enam_kabupaten_loro.csv')
    strat = read_csv(folder / 'stratified_cv.csv')

    assert len(source) == len(preds) == 127
    pred_by_key = {(r['kab_kota'], r['kecamatan']): r for r in preds}
    src_by_key = {(r['kab_kota'], r['kecamatan']): r for r in source}
    assert len(pred_by_key) == 127 and set(pred_by_key) == set(src_by_key)
    for key, srow in src_by_key.items():
        assert _preds_val_eq(pred_by_key[key]['harga_tanah_rata_rata_rp_m2'], srow['harga_tanah_rata_rata_rp_m2'])

    regions = {r['kab_kota'] for r in preds}
    assert len(regions) == 7 and len(audit['outer_folds']) == 7
    for entry in audit['outer_folds']:
        held = entry['test_region']
        assert held not in entry['train_regions']
        assert set(entry['train_regions']) == regions - {held}

    models_4f = [
        'OLS', 'KNN (k=5)', 'Decision Tree (d=4)',
        'GWR Fixed Gauss (lam=0)', 'GWR Fixed Gauss + Ridge',
        'GWR Adap Gauss (lam=0)', 'GWR Adap Gauss + Ridge', 'GWR Adap Bisq + Ridge',
    ]
    assert len(per_wilayah) == 7 * len(models_4f)
    ring_4f = {r['model']: r for r in ringkasan if r['fitur'] == '4_fitur_vif' and r['target'] == 'linear'}
    assert set(ring_4f) == set(models_4f)

    def _stats(rows, model):
        ys = [float(r['harga_tanah_rata_rata_rp_m2']) for r in rows]
        ps = [float(r[model]) for r in rows]
        assert all(math.isfinite(v) for v in ps)
        errs = [y - p for y, p in zip(ys, ps)]
        mae = sum(abs(e) for e in errs) / len(errs)
        rmse = math.sqrt(sum(e ** 2 for e in errs) / len(errs))
        mean_y = sum(ys) / len(ys)
        ss_tot = sum((y - mean_y) ** 2 for y in ys)
        r2 = 1.0 - sum(e ** 2 for e in errs) / ss_tot
        return mae, rmse, r2, sum(1 for p in ps if p < 0)

    no_solo = [r for r in preds if r['kab_kota'] != 'Kota Surakarta']
    solo = [r for r in preds if r['kab_kota'] == 'Kota Surakarta']
    for model in models_4f:
        mae127, rmse127, r2_127, neg = _stats(preds, model)
        mae122, rmse122, r2_122, _ = _stats(no_solo, model)
        mae_solo, _, _, _ = _stats(solo, model)
        row = ring_4f[model]
        assert math.isclose(mae127, float(row['MAE_127']), rel_tol=1e-10)
        assert math.isclose(rmse127, float(row['RMSE_127']), rel_tol=1e-10)
        assert math.isclose(r2_127, float(row['R2_127']), rel_tol=1e-10)
        assert math.isclose(mae122, float(row['MAE_122_tanpa_solo']), rel_tol=1e-10)
        assert math.isclose(rmse122, float(row['RMSE_122_tanpa_solo']), rel_tol=1e-10)
        assert math.isclose(r2_122, float(row['R2_122_tanpa_solo']), rel_tol=1e-10)
        assert math.isclose(mae_solo, float(row['MAE_surakarta']), rel_tol=1e-10)
        assert neg == int(row['prediksi_negatif'])
        block = {r['wilayah_uji']: r for r in per_wilayah if r['model'] == model}
        assert set(block) == regions
        for region in regions:
            reg_rows = [r for r in preds if r['kab_kota'] == region]
            rmae, rrmse, rr2, _ = _stats(reg_rows, model)
            assert int(block[region]['n']) == len(reg_rows)
            assert math.isclose(rmae, float(block[region]['MAE_Rp_m2']), rel_tol=1e-10)
            assert math.isclose(rrmse, float(block[region]['RMSE_Rp_m2']), rel_tol=1e-10)
            assert math.isclose(rr2, float(block[region]['R2']), rel_tol=1e-10)
    assert len(enam) == 12 and len(strat) == 18


def verify_rigor_stdlib(folder):
    """Verify advanced diagnostics folder using stdlib only."""
    if not __debug__:
        raise RuntimeError('Jalankan verifikasi tanpa python -O agar assertions aktif.')
    audit = json.loads((folder / 'audit.json').read_text(encoding='utf-8'))
    assert audit.get('status') == 'complete' and audit.get('protocol') == 'rigor_diagnostics_v1'
    required = [
        'block_bootstrap.csv', 'aoa_ringkasan.csv', 'aoa_per_kecamatan.csv',
        'moran_residual.csv', 'detail_prediksi_negatif.csv',
        'retransformasi_dan_nonnegatif.csv', 'kolinearitas_dan_kondisi.csv',
        'perbandingan_setara.csv', 'sensitivitas_titik.csv', 'peta_residual_lisa.png',
    ]
    for name in required:
        p = folder / name
        assert p.is_file() and p.stat().st_size > 0, f'Berkas diagnostik lanjut belum tersedia: {name}'
    boot = read_csv(folder / 'block_bootstrap.csv')
    assert len(boot) == 10
    for r in boot:
        assert float(r['MAE_127_ci_lo']) <= float(r['MAE_127']) <= float(r['MAE_127_ci_hi'])


def main():
    audit_dataset()
    sys.path.insert(0, str(ROOT))
    folder = ROOT / 'hasil/spasial' if (ROOT / 'hasil/spasial/audit.json').is_file() else ROOT / 'artifacts/spasial'
    try:
        from tanah.verification import verify
    except ModuleNotFoundError as exc:
        if exc.name not in {'numpy', 'pandas'}:
            raise
        print('Verifikasi CSV dengan pustaka standar; pelatihan model tidak dijalankan ulang.')
        verify_stdlib(folder)
    else:
        verify(folder, spatial=True)
    scores = read_csv(folder / 'metrik.csv')
    folds = read_csv(folder / 'per_wilayah.csv')
    predictions = read_csv(folder / 'prediksi_uji.csv')
    dataset = read_csv(prefer_hasil('hasil/paper/dataset_paper_2020.csv', 'artifacts/dataset_paper_2020.csv'))
    audit = json.loads((folder / 'audit.json').read_text(encoding='utf-8'))
    diagnostics = json.loads(prefer_hasil('hasil/paper/diagnostics.json', 'artifacts/figures/diagnostics.json').read_text(encoding='utf-8'))
    if audit['status'] != 'complete' or len(predictions) != 127 or len(folds) != 28 or len(dataset) != 127:
        raise ValueError('Hasil eksperimen atau dataset gabungan belum lengkap.')
    if not all(r['di_dalam_poligon'] == 'True' for r in dataset):
        raise ValueError('Ditemukan titik di luar poligon pada dataset_paper_2020.csv.')

    rigor_dir = ROOT / 'artifacts/diagnostik_lanjut'
    verify_rigor_stdlib(rigor_dir)
    boot_rows = read_csv(rigor_dir / 'block_bootstrap.csv')
    boot_map = {(r['skenario'], r['model']): r for r in boot_rows}
    aoa_rows = read_csv(rigor_dir / 'aoa_ringkasan.csv')
    moran_rows = read_csv(rigor_dir / 'moran_residual.csv')
    neg_detail_rows = read_csv(rigor_dir / 'detail_prediksi_negatif.csv')
    retrans_rows = read_csv(rigor_dir / 'retransformasi_dan_nonnegatif.csv')
    cond_rows = read_csv(rigor_dir / 'kolinearitas_dan_kondisi.csv')
    fair_rows = read_csv(rigor_dir / 'perbandingan_setara.csv')
    titik_rows = read_csv(rigor_dir / 'sensitivitas_titik.csv')

    regions = sorted({row['wilayah_uji'] for row in folds})
    lookup = {(row['wilayah_uji'], row['model']): row for row in folds}

    by_region = defaultdict(list)
    for row in dataset:
        by_region[row['kab_kota']].append(row)

    region_rows = []
    for region in regions:
        rs = by_region[region]
        prices = [float(r['harga_tanah_rata_rata_rp_m2']) for r in rs]
        pops = sum(int(r['jumlah_penduduk']) for r in rs)
        fas = sum(int(r['jumlah_fasum_regional']) for r in rs)
        area = sum(float(r['luas_km2']) for r in rs)
        region_rows.append([
            region, len(rs), rupiah(sum(prices) / len(prices)),
            f'{rupiah(min(prices))}–{rupiah(max(prices))}',
            rupiah(pops), str(fas), decimal_id(area, 2),
        ])

    price_s = describe_column(dataset, 'harga_tanah_rata_rata_rp_m2')
    pop_s = describe_column(dataset, 'jumlah_penduduk')
    fas_s = describe_column(dataset, 'jumlah_fasum_regional')
    area_s = describe_column(dataset, 'luas_km2')
    dist_s = describe_column(dataset, 'jarak_ke_batas_m')

    desc_table = table(
        ['Variabel / Atribut', 'Minimum', 'Median', 'Rata-rata', 'Maksimum', 'Simpangan baku'],
        [
            ['Harga tanah rata-rata (Rp/m²)', rupiah(price_s['min']), rupiah(price_s['median']),
             decimal_id(price_s['mean'], 2), rupiah(price_s['max']), decimal_id(price_s['std'], 2)],
            ['Jumlah penduduk (jiwa)', rupiah(pop_s['min']), rupiah(pop_s['median']),
             decimal_id(pop_s['mean'], 2), rupiah(pop_s['max']), decimal_id(pop_s['std'], 2)],
            ['Jumlah fasum regional (unit)', f"{fas_s['min']:.0f}", f"{fas_s['median']:.0f}",
             decimal_id(fas_s['mean'], 2), f"{fas_s['max']:.0f}", decimal_id(fas_s['std'], 2)],
            ['Luas poligon kecamatan (km²)', decimal_id(area_s['min'], 2), decimal_id(area_s['median'], 2),
             decimal_id(area_s['mean'], 2), decimal_id(area_s['max'], 2), decimal_id(area_s['std'], 2)],
            ['Jarak titik ke batas (m)', decimal_id(dist_s['min'], 2), decimal_id(dist_s['median'], 2),
             decimal_id(dist_s['mean'], 2), decimal_id(dist_s['max'], 2), decimal_id(dist_s['std'], 2)],
        ],
    )

    by_price = sorted(dataset, key=lambda r: float(r['harga_tanah_rata_rata_rp_m2']))
    low3 = '; '.join(
        f"{r['kecamatan']} ({r['kab_kota']}: Rp{rupiah(r['harga_tanah_rata_rata_rp_m2'])}/m², "
        f"penduduk {rupiah(r['jumlah_penduduk'])}, fasum {r['jumlah_fasum_regional']})"
        for r in by_price[:3]
    )
    high5 = '; '.join(
        f"{r['kecamatan']} ({r['kab_kota']}: Rp{rupiah(r['harga_tanah_rata_rata_rp_m2'])}/m², "
        f"penduduk {rupiah(r['jumlah_penduduk'])}, fasum {r['jumlah_fasum_regional']})"
        for r in reversed(by_price[-5:])
    )
    desc_text = (
        f"Kuartil harga tanah rata-rata pada 127 kecamatan adalah Q1 Rp{rupiah(price_s['q1'])}/m², "
        f"median Rp{rupiah(price_s['median'])}/m², dan Q3 Rp{rupiah(price_s['q3'])}/m². "
        f"Lima kecamatan dengan nilai tertinggi adalah {high5}. "
        f"Tiga kecamatan dengan nilai terendah adalah {low3}. "
        'Seluruh statistik ini bersifat deskriptif dan tidak digunakan untuk memasang standardisasi pada data uji.'
    )

    by_dist = sorted(dataset, key=lambda r: float(r['jarak_ke_batas_m']))
    closest, farthest = by_dist[0], by_dist[-1]
    max_pos_diff = max(float(r['selisih_point_on_surface_m']) for r in dataset)
    coord_audit_text = (
        f"Audit spasial pada 127 kecamatan menunjukkan seluruh 127 titik (100%) berada di dalam poligon "
        f"padanannya (`di_dalam_poligon = True`), dengan jarak titik ke batas berkisar antara "
        f"{decimal_id(closest['jarak_ke_batas_m'], 2)} m hingga {decimal_id(farthest['jarak_ke_batas_m'], 2)} m "
        f"(median {decimal_id(dist_s['median'], 2)} m; rata-rata {decimal_id(dist_s['mean'], 2)} m) "
        f"dan selisih numerik maksimum point-on-surface terhadap Shapely sekitar {f'{max_pos_diff:.2e}'.replace('.', ',')} m."
    )
    coord_audit_table = table(
        ['Kasus ekstrem jarak ke batas', 'Kabupaten/kota', 'Kecamatan', 'Jarak ke batas (m)', 'Luas kecamatan (km²)'],
        [
            ['Terdekat ke batas', closest['kab_kota'], closest['kecamatan'],
             decimal_id(closest['jarak_ke_batas_m'], 2), decimal_id(closest['luas_km2'], 2)],
            ['Terjauh dari batas', farthest['kab_kota'], farthest['kecamatan'],
             decimal_id(farthest['jarak_ke_batas_m'], 2), decimal_id(farthest['luas_km2'], 2)],
        ],
    )

    # Dual-metric main table with 95% Block-Bootstrap CI
    score_by_m = {r['model']: r for r in scores}
    main_metric_rows = []
    for m in MODELS:
        b = boot_map['2_fitur_utama', m]
        s = score_by_m[m]
        delta_str = 'Acuan (0)' if m == 'Linear' else (
            f"{signed_rupiah(b['delta_MAE_127_vs_ref'])} "
            f"[{signed_rupiah(b['delta_MAE_127_ci_lo'])}; {signed_rupiah(b['delta_MAE_127_ci_hi'])}]"
        )
        main_metric_rows.append([
            m,
            f"{rupiah(s['MAE_Rp_m2'])} [{rupiah(b['MAE_127_ci_lo'])}–{rupiah(b['MAE_127_ci_hi'])}]",
            f"{rupiah(s['RMSE_Rp_m2'])} [{rupiah(b['RMSE_127_ci_lo'])}–{rupiah(b['RMSE_127_ci_hi'])}]",
            decimal_id(s['R2'], 3),
            delta_str,
            f"{rupiah(b['MAE_122_tanpa_solo'])} [{rupiah(b['MAE_122_ci_lo'])}–{rupiah(b['MAE_122_ci_hi'])}] ({decimal_id(b['R2_122_tanpa_solo'], 3)})",
        ])

    neg_2f_rows = [r for r in neg_detail_rows if r['spesifikasi'] == '2 fitur utama (Bagian 4)']
    neg_table_str = table(
        ['Model', 'Jumlah (%)', 'Prediksi terendah (Rp/m²)', 'Median negatif (Rp/m²)', 'Sebaran kabupaten & contoh ekstrem'],
        [
            [
                r['model'],
                f"{r['jumlah_negatif']}/127 ({decimal_id(r['persen_negatif'], 1)}%)",
                f"−{rupiah(abs(float(r['min_prediksi_Rp'])))}" if int(r['jumlah_negatif']) > 0 else rupiah(r['min_prediksi_Rp']) + ' (positif)',
                f"−{rupiah(abs(float(r['median_negatif_Rp'])))}" if int(r['jumlah_negatif']) > 0 else 'Tidak ada',
                f"{r['wilayah_terdampak']}; contoh: {r['contoh_kecamatan_ekstrem'].replace('-', '−')}" if int(r['jumlah_negatif']) > 0 else 'Seluruh prediksi positif',
            ]
            for r in neg_2f_rows
        ],
    )

    values = {
        'REGION_COUNTS': table(
            ['Kabupaten/kota', 'n', 'Rata-rata harga (Rp/m²)', 'Rentang harga (Rp/m²)',
             'Total penduduk', 'Total fasum', 'Total luas (km²)'],
            region_rows,
        ),
        'TARGET_VALIDITY_TABLE': table(
            ['Dimensi validitas target', 'Status bukti pada repositori', 'Implikasi metodologis & batas klaim'],
            [
                ['Definisi konseptual label harga', 'Dilabeli harga tanah rata-rata (Rp/m²) di Lampiran A Salim Aziz; artikel Aziz dkk. (2023) hlm. 147 menyebut Bhumi ATR-BPN 2020',
                 'Belum dipastikan apakah angka mewakili nilai zona ZNT, harga penawaran, transaksi riil, atau NJOP; tidak boleh diklaim sebagai harga pasar transaksi'],
                ['Metode agregasi ke kecamatan', 'Rumus perataan poligon/bidang ke 127 angka kecamatan tidak tercantum pada lampiran maupun artikel sumber',
                 'Potensi bias agregasi (rata-rata sederhana vs tertimbang luas) tidak teramati; evaluasi diperlakukan sebagai prediksi indeks sekunder tingkat kecamatan'],
                ['Ukuran sampel / poligon per kecamatan', 'Jumlah zona atau titik sampel pembentuk rata-rata per kecamatan (nᵢ) tidak tersedia di arsip publik',
                 'Presisi label antar-kecamatan mungkin tidak seragam (heteroskedastisitas galat pengukuran label)'],
                ['Tahun efektif pengukuran', 'Judul tabel lampiran menyatakan tahun 2020; arsip historis layer Bhumi 2020 dan tanggal pemutakhiran zona belum diperoleh',
                 'Kemungkinan jeda pembaruan antarzona di portal asal membatasi penafsiran lintas waktu'],
                ['Integritas transkripsi sekunder', '127/127 pasangan wilayah dan 381/381 nilai numerik cocok 100% dengan PDF Lampiran A (SHA-256 terverifikasi)',
                 'Bebas salah salin dari sumber sekunder, tetapi kecocokan salinan tidak menggantikan validasi pengukuran primer'],
            ],
        ),
        'TEMPORAL_ALIGNMENT_TABLE': table(
            ['Sumber data', 'Variabel yang diturunkan', 'Tahun acuan amatan', 'Versi / tahun arsip', 'Risiko ketidakselarasan & galat proksi'],
            [
                ['Lampiran A Salim Aziz (UNS)', 'Harga rata-rata (target), penduduk, fasum regional', '2020', ' Publikasi artikel 2023',
                 'Metode agregasi harga Bhumi 2020 belum terverifikasi; terdapat selisih total fasum/penduduk terhadap tabel ringkas artikel'],
                ['BIG KSP Satu Peta (Layer 3)', 'Batas poligon, luas proksi, titik ST_PointOnSurface', 'Batas efektif pasca-2019', 'Metadata 20230928 (edisi 2022)',
                 'Seluruh 127 kecamatan sudah terbentuk sebelum 2020, tetapi kesamaan garis batas mikro 2020 vs 2023 belum terverifikasi'],
                ['ESA WorldCover 10 m', 'Persentase terbangun, tanaman budidaya, tutupan pohon', '2020', 'v100 (Zanaga dkk., 2021)',
                 'Selaras tahun 2020; ketidakpastian berasal dari salah klasifikasi piksel 10 m dan irisan piksel tepi batas'],
                ['OpenStreetMap (Geofabrik)', 'Jarak garis lurus wisata/kampus & hitungan radius 5 km', '1 Januari 2021', 'Ekstrak 210101',
                 'Selisih 1 hari pasca-2020; bias kelengkapan pemetaan sukarela, duplikasi objek institusi, dan bukan jarak jaringan jalan raya'],
                ['SRTM Digital Elevation', 'Median elevasi dan kemiringan lereng kecamatan', 'Februari 2000', 'CIAT v4.1 (~90 m)',
                 'Topografi makro relatif stabil dalam dua dekade, tetapi meratakan variasi lereng mikro permukiman'],
            ],
        ),
        'VARIABLES': table(['Komponen', 'Kolom', 'Definisi'], [
            ['Target', 'harga_tanah_rata_rata_rp_m2', 'Harga rata-rata kecamatan 2020, Rp/m² (metrik keputusan utama)'],
            ['Prediktor konfirmatori 1', 'jumlah_penduduk', 'Jumlah penduduk kecamatan pada tabel sumber, jiwa'],
            ['Prediktor konfirmatori 2', 'jumlah_fasum_regional', 'Jumlah fasilitas umum regional pada tabel sumber, unit'],
            ['Lokasi GWR', 'lat, lon', 'Titik interior ST_PointOnSurface WGS84 dari proyeksi UTM 49S'],
            ['Kelompok validasi', 'kab_kota', 'Tujuh blok administratif untuk LOKO luar dan validasi dalam'],
        ]),
        'DESCRIPTIVE': desc_table + '\n\n' + desc_text,
        'COORDINATE_AUDIT': coord_audit_text + '\n\n' + coord_audit_table,
        'EXPERIMENT_HIERARCHY': table(
            ['Kelompok eksperimen', 'Bagian', 'Status inferensi', 'Fitur & skala target', 'Tujuan metodologis'],
            [
                ['Eksperimen utama terkunci', 'Bagian 4', 'Konfirmatori utama', '2 fitur sumber; target linear Rp/m²',
                 'Menguji hipotesis manfaat pembobotan geografis lintas kabupaten tanpa rekayasa fitur pasca-uji'],
                ['Replikasi & perluasan tutupan lahan', 'Bagian 6.3–6.4', 'Eksploratif terjadwal', '7 fitur (WorldCover + kepadatan); target ln(harga)',
                 'Menguji kontribusi tutupan lahan 2020 dan mereplikasi protokol notebook secara terkendali'],
                ['Uji hipotesis akses & topografi', 'Bagian 6.5–6.6', 'Eksploratif pasca-galat', '8–11 fitur (OSM + SRTM); ln(harga) & Rp/m² potong nol',
                 'Memeriksa apakah galat lokal (mis. Tawangmangu) berkaitan dengan wisata, kampus, dan lereng'],
                ['Diagnostik sensitivitas & keadilan protokol', 'Bagian 6.7–6.8', 'Diagnostik metodologis', 'Saringan VIF, Duan smearing, Poisson QMLE, 4 titik lokasi',
                 'Mengisolasi efek kolinearitas lokal, bias retransformasi log, prediksi negatif, domain shift, dan keadilan tuning'],
            ],
        ),
        'MODEL_PROTOCOL_MATRIX': table(
            ['Model', 'Ruang parameter (eksperimen utama)', 'Ruang parameter (benchmark setara §6.8)', 'Pra-pemrosesan dalam-lipatan', 'Penalti & kendala dasar'],
            [
                ['Linear / Ridge Global', 'Tanpa parameter (OLS murni)', 'λ ∈ {0; 0,01; 0,1; 1; 10} tanpa penalti intersep',
                 'Standardisasi z-score data latih', 'Tanpa penalti di §4; Ridge L2 di §6.8'],
                ['KNN', 'k ∈ {3, 7, 15}, bobot invers jarak Euclidean', 'k ∈ {3, 5, 7, 15}, bobot invers jarak Euclidean',
                 'Standardisasi z-score data latih', 'Nonparametrik; otomatis positif karena kombinasi konveks y latih'],
                ['Decision Tree (CART)', 'max_depth ∈ {2, 4, 6}, min_samples_leaf=3', 'max_depth ∈ {2, 4, 6}, min_samples_leaf=3',
                 'Standardisasi z-score data latih (invarian urutan)', 'Otomatis positif karena rerata daun data latih'],
                ['Classic GWR', 'Fixed Gaussian h ∈ {5, 10, 20, 40} km', 'Fixed h ∈ {5..80} km atau Adaptive k ∈ {15..80} + λ ∈ {0..10}',
                 'Standardisasi z-score latih + jarak Haversine WGS84', 'Tanpa ridge (tolak singular) di §4; Ridge lokal bebas intersep di §6.7–6.8'],
            ],
        ),
        'METRICS': table(
            ['Model', 'MAE 127 kec. [95% CI blok]', 'RMSE 127 kec. [95% CI blok]', 'R² (127)', 'ΔMAE vs Linear [95% CI blok]', 'Enam kab. 122 kec. MAE [95% CI] (R²)'],
            main_metric_rows,
        ),
        'REGIONAL_MAE': table(['Wilayah', 'n', 'Linear', 'KNN', 'Tree', 'GWR'],
                              [[region, lookup[region, 'GWR']['n'],
                                *[rupiah(lookup[region, model]['MAE_Rp_m2']) for model in MODELS]] for region in regions])
                        + '\n\nSeluruh MAE pada tabel dalam Rp/m²; n adalah jumlah kecamatan uji.',
        'REGIONAL_RMSE': table(['Wilayah', 'n', 'Linear', 'KNN', 'Tree', 'GWR'],
                               [[region, lookup[region, 'GWR']['n'],
                                 *[rupiah(lookup[region, model]['RMSE_Rp_m2']) for model in MODELS]] for region in regions])
                         + '\n\nSeluruh RMSE pada tabel dalam Rp/m²; n adalah jumlah kecamatan uji.',
        'AOA_TABLE': table(
            ['Ruang prediktor', 'Luar AoA total (%)', 'Surakarta luar AoA', '6 kab. luar AoA', 'Median DI Solo vs 6 kab. (ambang)', 'MAE GWR dalam vs luar AoA (Rp/m²)'],
            [
                [
                    r['ruang_fitur'],
                    f"{r['n_luar_AoA']}/127 ({decimal_id(r['pct_luar_AoA'], 1)}%)",
                    f"{r['n_solo_luar_AoA']}/5",
                    f"{r['n_nonsolo_luar_AoA']}/122",
                    f"{decimal_id(r['median_DI_solo'], 2)} vs {decimal_id(r['median_DI_nonsolo'], 2)} ({decimal_id(r['median_ambang'], 2)})",
                    f"{rupiah(r['MAE_GWR_dalam_AoA'])} vs {rupiah(r['MAE_GWR_luar_AoA'])}",
                ]
                for r in aoa_rows
            ],
        ),
        'PARAMETERS': table(['Wilayah uji', 'k KNN', 'Kedalaman Tree', 'Bandwidth GWR (km)'],
                            [[region, *[int(float(lookup[region, model]['parameter'])) for model in MODELS[1:]]] for region in regions]),
        'NEGATIVE_TABLE': neg_table_str,
        'MORAN_TABLE': table(
            ['Skenario', 'Model / Variabel', "Global Moran's I", 'z-score (p permutasi)', 'Klaster LISA sig. (p<0,05)', 'Rincian (HH / LL / HL / LH)'],
            [
                [
                    r['skenario'],
                    r['model'],
                    decimal_id(r['moran_I'], 3),
                    f"{decimal_id(r['z_score'], 2)} ({decimal_id(r['p_permutasi'], 4)})",
                    f"{r['n_klaster_sig']}/127",
                    f"{r['HH']} / {r['LL']} / {r['HL']} / {r['LH']}",
                ]
                for r in moran_rows
            ],
        ),
        'MAP_FIGURE': '![Gambar 1. Harga aktual dan prediksi out-of-fold eksperimen utama dua prediktor; skala warna seragam, batas BIG berpenanda lebih baru daripada 2020.](../artifacts/figures/peta_harga_dan_prediksi.png)',
        'SCATTER_FIGURE': '![Gambar 2. Harga aktual terhadap prediksi uji 127 kecamatan pada eksperimen utama. Garis putus-putus menunjukkan prediksi tepat.](../artifacts/figures/aktual_prediksi.png)',
        'RESIDUAL_MAP_FIGURE': '![Gambar 3. Peta residual out-of-fold dan klaster Local Moran (LISA) signifikan pada 127 kecamatan: perbandingan GWR dua fitur utama dengan GWR Adaptive+Ridge empat fitur non-kolinear.](../artifacts/diagnostik_lanjut/peta_residual_lisa.png)',
        'CANDIDATE_SOURCES': table(['Variabel pengembangan', 'Kandidat sumber resmi', 'Catatan verifikasi & tahun data'], [
            ['Kepadatan penduduk (jiwa/km²)', 'BPS (SP2020 / Publikasi Dalam Angka) dan luas poligon UTM 49S (luas_km2)',
             'Periksa tahun tabel penduduk agar mewakili 2020 dan cocok untuk 22 kecamatan Boyolali.'],
            ['Fasilitas umum regional', 'Lampiran Aziz (tahun data 2020; tahun publikasi belum dipastikan), BPS/Podes, dan instansi penyedia',
             'Definisikan kategori fasum secara konsisten; Podes 2021 bukan data 2020 sehingga hanya dipakai jika dinyatakan sebagai pendekatan.'],
            ['Akses pusat kegiatan (km)', 'Dokumen RTRW Provinsi Jawa Tengah / RTRW Kabupaten/Kota',
             'Tetapkan pusat kegiatan secara independen tanpa memakai nilai harga tanah tertinggi pada dataset.'],
            ['Akses jalan utama & waktu tempuh', 'BIG / Peta Rupabumi Indonesia (RBI), jaringan jalan OSRM, dan dinas terkait',
             'Ganti jarak garis lurus dengan jarak/waktu tempuh jaringan jalan sesuai klasifikasi arteri/kolektor tahun 2020.'],
            ['Proporsi permukaan terbangun (%)', 'ESA WorldCover 2020 v100 (diolah) dan GHSL GHS-BUILT-S R2023A epoch 2020 (alternatif)',
             'ESA WorldCover 2020 v100 sudah diolah dan diuji secara eksploratif pada bagian 6.3–6.8; GHSL tetap menjadi alternatif pembanding.'],
        ]),
        'FUTURE_EXPERIMENTS': table(['Tahap', 'Spesifikasi', 'Status'], [
            ['A', 'Jumlah penduduk + fasilitas regional (protokol terkunci)', 'Selesai; acuan konfirmatori utama pada Bagian 4'],
            ['B', 'Kepadatan penduduk + fasilitas regional + tutupan lahan', 'Diuji eksploratif pada Bagian 6.4 dan disaring via VIF pada Bagian 6.7–6.8'],
            ['C', 'B + akses pusat kegiatan + jaringan jalan + fasilitas', 'Sebagian diuji pasca-galat pada Bagian 6.5–6.6 (OSM garis lurus & SRTM); perlu validasi data independen'],
            ['D', 'Sensitivitas titik representatif kecamatan', 'Selesai diuji pada 4 alternatif titik di Bagian 6.8; titik berbobot populasi persil belum tersedia'],
        ]),
        'AUDIT_STATUS': table(['Komponen', 'Status saat ini', 'Bukti di repositori / tindakan audit lanjutan'], [
            ['Konsistensi komputasional & ketidakpastian blok', 'Terverifikasi',
             '127 prediksi uji, 7 blok, 28 baris per_wilayah, serta 10 berkas diagnostik lanjut (bootstrap blok, AoA, Moran/LISA, Duan, Poisson QMLE) diverifikasi otomatis sebelum naskah dibuat.'],
            ['Ketercakupan interior & sensitivitas titik GWR', 'Terverifikasi pada 4 representasi titik',
             '127/127 titik BIG ST_PointOnSurface berada di dalam poligon (jarak ke batas 383,02–4.572,15 m); uji sensitivitas terhadap centroid BIG, titik BPS/HDX, dan titik GADM menunjukkan peringkat model tidak berubah.'],
            ['Padanan nama wilayah (padanan_nama.csv)', '125 otomatis + 2 eksplisit; cocok kode Kemendagri',
             'Kebakkramat–Kebakramat dan Sidoharjo–Sidoarjo cocok kode resmi Kemendagri/BPS tanpa benturan kunci; konfirmasi batas mikro historis tetap diperlukan.'],
            ['Kesesuaian garis batas historis tahun 2020', 'Belum terverifikasi garis mikro',
             'Seluruh 127 kecamatan telah terbentuk sebelum 2020 (pemekaran Boyolali efektif 2019), namun arsip poligon BIG berpenanda fitur 20230928 (edisi 2022).'],
            ['Definisi & angka primer harga tanah 2020', '381/381 nilai cocok dengan PDF; pengukuran primer belum tervalidasi',
             'Perlu konfirmasi ke ATR/BPN atau penulis sumber mengenai jenis harga (ZNT/penawaran/transaksi/NJOP), jumlah poligon/sampel per kecamatan, dan rumus agregasi. Klaim praktis dibatasi ketat.'],
        ]),
        'CONTRIBUTIONS': table(['Anggota', 'Peran dan kontribusi penelitian'], [
            ['Yashif Victoriawan', 'Integrasi arsitektur program, validasi bersarang, dan reproduksi eksperimen utama'],
            ['Queen Nika Prahara Mutiara Phasya', 'Audit sumber harga sekunder, rekonsiliasi lampiran PDF, dan validitas variabel'],
            ['Syaikhasril Maulana Firdaus', 'Audit geometri multi-sumber, pengolahan data pendukung, serta diagnostik statistik dan sensitivitas GWR'],
            ['Azzaral Aswad Asshiddiqy', 'Analisis galat lintas wilayah, evaluasi autokorelasi spasial, dan penyusunan pembahasan'],
        ]),
    }

    source_rows = read_csv(ROOT / 'artifacts/data_audit/perbandingan_fasum.csv')
    values['SOURCE_AUDIT'] = (
        'Total fasilitas pada lampiran berbeda dari penjumlahan kategori Tabel 3 artikel Aziz dkk. (2023), '
        'hlm. 149, pada seluruh tujuh wilayah. Artikel menyebut observasi peneliti 2023 dengan data 2020. '
        'Perbedaan belum dapat ditentukan sebagai salah ketik, beda versi, atau beda cakupan. CSV acuan '
        'dipertahankan agar hasil eksperimen dapat ditelusuri.\n\n'
        + table(['Wilayah', 'Fasum CSV/lampiran', 'Fasum artikel', 'Selisih CSV − artikel'],
                [[r['kab_kota'], r['fasum_csv'], r['fasum_artikel'], r['selisih_csv_minus_artikel']]
                 for r in source_rows])
        + '\n\nJumlah penduduk CSV juga berbeda dari total urban dan rural Tabel 1 artikel pada Surakarta '
        '(522.364 dibanding 576.412), Sukoharjo (911.966 dibanding 907.587), dan Karanganyar '
        '(938.808 dibanding 931.963). Empat wilayah lainnya cocok. Lima angka kecamatan Surakarta '
        'cocok dengan Gambar 1.10 laporan Pemerintah Kota Surakarta, hlm. i-20, yang mengutip BPS 2021 '
        'untuk tahun data 2020. Pemeriksaan ini tidak menggantikan verifikasi seluruh kecamatan ke BPS. '
        'Rincian bukti, URL, dan kebutuhan rekonsiliasi tersedia di data/SUMBER_DATASET.md; '
        'perbandingan dapat diulang dengan scripts/audit_dataset.py.'
    )

    candidates = read_csv(ROOT / 'data/kandidat_variabel.csv')
    values['CANDIDATE_REGISTRY'] = table(
        ['No.', 'Kandidat variabel', 'Landasan konsep', 'Prioritas pengumpulan'],
        [[i, row['variabel'], row['referensi'], row['prioritas']]
         for i, row in enumerate(candidates, 1)],
    )

    solo = 'Kota Surakarta'
    shares = diagnostics['surakarta_share_squared_error']
    values['SURAKARTA_DISCUSSION'] = (
        f"Sebagai uji tekan perkotaan (*urban stress test*), Kota Surakarta hanya memuat lima kecamatan, "
        f"tetapi menghasilkan MAE GWR Rp{rupiah(lookup[solo, 'GWR']['MAE_Rp_m2'])}/m² "
        f"dan KNN Rp{rupiah(lookup[solo, 'KNN']['MAE_Rp_m2'])}/m² (Linear Rp{rupiah(lookup[solo, 'Linear']['MAE_Rp_m2'])}/m²; "
        f"Decision Tree Rp{rupiah(lookup[solo, 'Decision Tree']['MAE_Rp_m2'])}/m²). "
        f"Lima kecamatan ini menyumbang sekitar {decimal_id(100 * shares['GWR'], 1)}% jumlah kuadrat galat GWR "
        f"dan {decimal_id(100 * shares['KNN'], 1)}% jumlah kuadrat galat KNN. "
        'Ketika lima kecamatan Surakarta dipisahkan dari ringkasan (122 kecamatan pada enam kabupaten), '
        'KNN mencatat MAE terendah Rp525.199/m² dan regresi linear mencatat RMSE terendah Rp875.922/m² (R² 0,602), '
        'sedangkan GWR tetap berada di belakang regresi linear (MAE Rp614.052/m²; ΔMAE +Rp32.120/m², '
        '95% CI blok [+Rp8.491; +Rp51.807]/m²). Dominasi galat di Surakarta terjadi karena premi aglomerasi kota inti '
        'tidak terwakili oleh profil keenam kabupaten latih.'
    )

    analysis = ROOT / 'artifacts/analisis_variabel'
    profiles = read_csv(analysis / 'statistik_variabel.csv')
    target = 'harga_tanah_rata_rata_rp_m2'
    summary_rows = []
    for profile in profiles:
        digits = 3 if profile['satuan'] == 'unit/km²' else 2 if profile['satuan'] == '%' else 0
        low, q1, med, q3, high = [decimal_id(profile[key], digits) for key in ('min', 'q1', 'median', 'q3', 'max')]
        summary_rows.append([f"{profile['label']} ({profile['satuan']})", med, f'{q1}–{q3}', low, high])
    values['STATISTIK_VARIABEL'] = table(['Variabel (satuan)', 'Median', 'Q1–Q3', 'Min.', 'Maks.'], summary_rows)
    labels = {row['variabel']: row['label'] for row in profiles}
    pairs = read_csv(analysis / 'korelasi_pasangan.csv')
    values['KORELASI_HARGA'] = table(['Prediktor terhadap harga 2020', 'Pearson r', 'Spearman ρ'],
        [[labels[r['variabel_x']], decimal_id(r['pearson'], 3), decimal_id(r['spearman'], 3)]
         for r in pairs if r['variabel_y'] == target and r['variabel_x'] != target])

    akses = read_csv(ROOT / 'artifacts/akses_medan/metrik.csv')
    review = ROOT / 'artifacts/review_kepadatan_wisata'
    review_preds = read_csv(review / 'prediksi_uji.csv')
    review_sel = read_csv(review / 'prediksi_seleksi.csv')
    zero_counts = defaultdict(int)
    for row in review_preds:
        if float(row['prediksi']) == 0.0:
            zero_counts[(row['model'], row['spesifikasi'])] += 1
    zero_seleksi = sum(1 for row in review_sel if float(row['prediksi_seleksi']) == 0.0)
    values['UJI_KORELASI'] = table(
        ['Variabel', 'Pearson', 'Spearman', 'Dalam blok', 'p terkoreksi'],
        [[r['variabel'], *[decimal_id(r[c], 4) for c in ('pearson', 'spearman', 'rho_dalam_blok', 'p_bonferroni')]]
         for r in read_csv(review / 'korelasi.csv')])
    values['UJI_SELEKSI'] = table(
        ['Model', 'Spesifikasi', 'MAE (Rp/m²)', 'RMSE (Rp/m²)', 'Prediksi nol'],
        [[r['model'], r['spesifikasi'], rupiah(r['MAE_Rp_m2']), rupiah(r['RMSE_Rp_m2']),
          f"{zero_seleksi}/127" if r['model'] == 'Seleksi RMSE' else f"{zero_counts[(r['model'], r['spesifikasi'])]}/127"]
         for r in read_csv(review / 'metrik.csv') if r['spesifikasi'] in ('kota_wisata_medan', 'validasi internal')])
    values['ZERO_CLIP_SUMMARY'] = (
        f"Berbeda dari eksperimen konfirmatori dua prediktor pada Bagian 4 yang mempertahankan nilai negatif tanpa pemotongan, "
        f"eksperimen eksploratif pada bagian ini menetapkan batas bawah Rp0/m². Pemotongan terjadi pada "
        f"{zero_counts[('Ridge', 'kota_wisata_medan')]}/127 kecamatan untuk Ridge lima variabel, "
        f"{zero_counts[('GWR ridge', 'kota_wisata_medan')]}/127 untuk GWR ridge lima variabel, "
        f"dan {zero_seleksi}/127 untuk Seleksi RMSE (total {sum(zero_counts.values())} dari {rupiah(len(review_preds))} prediksi uji "
        f"pada seluruh kombinasi model dan spesifikasi)."
    )
    values['HASIL_AKSES'] = table(
        ['Prediktor', 'KNN', 'Pohon', 'Ridge global', 'GWR ridge'],
        [[spec] + [rupiah(next(r['MAE_Rp_m2'] for r in akses
                              if r['spesifikasi'] == spec and r['model'] == model))
                   for model in ('KNN', 'Pohon', 'Ridge global', 'GWR ridge')]
         for spec in dict.fromkeys(r['spesifikasi'] for r in akses)])
    values['FIGUR_TUJUH_PREDIKTOR'] = '../artifacts/tujuh_prediktor_big/evaluasi.png'
    extended = ROOT / 'artifacts/tujuh_prediktor_big'
    replica = ROOT / 'artifacts/replikasi_notebook'
    for path in (extended, replica):
        verify_stdlib(path, colab=True)
    ext_scores = sorted(read_csv(extended / 'metrik.csv'), key=lambda r: float(r['MAE_Rp_m2']))
    values['COLAB_METRICS'] = table(['Model', 'MAE (Rp/m²)', 'RMSE (Rp/m²)', 'MAPE (%)', 'R²'],
        [[r['model'], rupiah(r['MAE_Rp_m2']), rupiah(r['RMSE_Rp_m2']),
          decimal_id(r['MAPE_pct']), decimal_id(r['R2'], 3)] for r in ext_scores])

    sens_dir = ROOT / 'artifacts/sensitivitas_gwr'
    verify_sensitivity_stdlib(sens_dir)
    ringkasan_rows = read_csv(sens_dir / 'ringkasan_loro.csv')
    ring_map = {(r['fitur'], r['target'], r['model']): r for r in ringkasan_rows}
    sens_items = [
        ('7_fitur', 'log', 'OLS', '7 fitur (log): OLS'),
        ('7_fitur', 'log', 'KNN (k=5)', '7 fitur (log): KNN (k=5)'),
        ('7_fitur', 'log', 'Decision Tree (d=4)', '7 fitur (log): Decision Tree (d=4)'),
        ('7_fitur', 'log', 'GWR Fixed Gauss (lam=1e-3, notebook)', '7 fitur (log): GWR Fixed (notebook)'),
        ('7_fitur', 'log', 'GWR Adap Gauss + Ridge', '7 fitur (log): GWR Adap Gauss + Ridge'),
        ('7_fitur', 'log', 'GWR Adap Bisq + Ridge', '7 fitur (log): GWR Adap Bisq + Ridge'),
        ('7_fitur', 'linear', 'OLS', '7 fitur (linear): OLS'),
        ('7_fitur', 'linear', 'KNN (k=5)', '7 fitur (linear): KNN (k=5)'),
        ('7_fitur', 'linear', 'GWR Fixed Gauss + Ridge', '7 fitur (linear): GWR Fixed + Ridge'),
        ('7_fitur', 'linear', 'GWR Adap Gauss + Ridge', '7 fitur (linear): GWR Adap Gauss + Ridge'),
        ('4_fitur_vif', 'linear', 'OLS', '4 fitur VIF (linear): OLS'),
        ('4_fitur_vif', 'linear', 'KNN (k=5)', '4 fitur VIF (linear): KNN (k=5)'),
        ('4_fitur_vif', 'linear', 'Decision Tree (d=4)', '4 fitur VIF (linear): Decision Tree (d=4)'),
        ('4_fitur_vif', 'linear', 'GWR Fixed Gauss + Ridge', '4 fitur VIF (linear): GWR Fixed + Ridge'),
        ('4_fitur_vif', 'linear', 'GWR Adap Gauss + Ridge', '4 fitur VIF (linear): GWR Adap Gauss + Ridge'),
        ('4_fitur_vif', 'linear', 'GWR Adap Bisq + Ridge', '4 fitur VIF (linear): GWR Adap Bisq + Ridge'),
    ]
    values['GWR_SENSITIVITY_TABLE'] = table(
        ['Spesifikasi & Model', 'MAE 127 (Rp/m²)', 'RMSE 127 (Rp/m²)', 'R² 127 (Neg.)', 'MAE 122 / Solo (Rp/m²)'],
        [
            [
                label,
                rupiah(ring_map[k]['MAE_127']),
                rupiah(ring_map[k]['RMSE_127']),
                f"{decimal_id(ring_map[k]['R2_127'], 3)} ({ring_map[k]['prediksi_negatif']})",
                f"{rupiah(ring_map[k]['MAE_122_tanpa_solo'])} / {rupiah(ring_map[k]['MAE_surakarta'])}",
            ]
            for *k_parts, label in sens_items
            for k in [tuple(k_parts)]
        ],
    )

    wilayah_4f = {(r['wilayah_uji'], r['model']): r for r in read_csv(sens_dir / 'per_wilayah_4fitur_linear.csv')}

    def _short_param(p):
        return p.replace('bw=', '').replace(';lambda=', ', λ=')

    values['GWR_REGIONAL_4FITUR'] = table(
        ['Wilayah uji', 'n', 'OLS (Rp/m²)', 'KNN k=5 (Rp/m²)', 'GWR Fixed+R', 'GWR Adap+R'],
        [
            [
                region,
                wilayah_4f[region, 'OLS']['n'],
                rupiah(wilayah_4f[region, 'OLS']['MAE_Rp_m2']),
                rupiah(wilayah_4f[region, 'KNN (k=5)']['MAE_Rp_m2']),
                f"{rupiah(wilayah_4f[region, 'GWR Fixed Gauss + Ridge']['MAE_Rp_m2'])} ({_short_param(wilayah_4f[region, 'GWR Fixed Gauss + Ridge']['parameter'])})",
                f"{rupiah(wilayah_4f[region, 'GWR Adap Gauss + Ridge']['MAE_Rp_m2'])} ({_short_param(wilayah_4f[region, 'GWR Adap Gauss + Ridge']['parameter'])})",
            ]
            for region in regions
        ],
    )

    enam_map = {(r['fitur'], r['target'], r['model']): r for r in read_csv(sens_dir / 'enam_kabupaten_loro.csv')}
    strat_map = {(r['fitur'], r['target'], r['model']): r for r in read_csv(sens_dir / 'stratified_cv.csv')}
    domain_models = ['OLS', 'KNN (k=5)', 'Decision Tree (d=4)', 'GWR Fixed Gauss + Ridge', 'GWR Adap Gauss + Ridge', 'GWR Adap Bisq + Ridge']
    domain_rows = []
    for feat, scale, tag in [('7_fitur', 'log', '7 fitur (log)'), ('4_fitur_vif', 'linear', '4 fitur VIF (linear)')]:
        for model in domain_models:
            loro_model = 'GWR Fixed Gauss (lam=1e-3, notebook)' if (feat == '7_fitur' and model == 'GWR Fixed Gauss + Ridge') else model
            r_loro = ring_map[feat, scale, loro_model]
            r_enam = enam_map[feat, scale, model]
            r_strat = strat_map[feat, scale, model]
            suffix = '*' if loro_model != model else ''
            domain_rows.append([
                f'{tag}: {model}{suffix}',
                f"{rupiah(r_loro['MAE_127'])} ({decimal_id(r_loro['R2_127'], 3)})",
                f"{rupiah(r_enam['MAE_122'])} ({decimal_id(r_enam['R2_122'], 3)})",
                f"{rupiah(r_strat['MAE_127'])} ({decimal_id(r_strat['R2_127'], 3)})",
                f"{r_loro['prediksi_negatif']} / {r_enam['prediksi_negatif']} / {r_strat['prediksi_negatif']}",
            ])
    values['GWR_DOMAIN_SHIFT_TABLE'] = table(
        ['Spesifikasi & Model', 'LORO 127 MAE (R²)', 'LORO 122 latih ulang MAE (R²)', 'Stratified 5-Fold MAE (R²)', 'Neg. (127/122/Strat)'],
        domain_rows,
    )

    # New Section 6.8 tables: Collinearity/Local Condition Number, Target Treatment/Duan/Poisson, Fair Benchmark, Point Sensitivity
    values['COLLINEARITY_TABLE'] = table(
        ['Spesifikasi GWR', 'Fitur', 'VIF maks (global / latih)', 'κ lokal median (P90)', 'κ lokal maks', 'Lokasi κ > 30'],
        [
            [
                r['spesifikasi'].replace(' — ', ': '),
                r['jumlah_fitur'],
                f"{decimal_id(r['VIF_maks_global'], 2)} / {decimal_id(r['VIF_maks_latih_tertinggi'], 2)}",
                f"{decimal_id(r['kappa_lokal_median'], 2)} ({decimal_id(r['kappa_lokal_p90'], 2)})",
                decimal_id(r['kappa_lokal_maks'], 2),
                f"{r['n_lokasi_kappa_gt_30']}/127",
            ]
            for r in cond_rows
        ],
    )

    retrans_4f7f = [r for r in retrans_rows if r['fitur'] in ('4_fitur_vif', '7_fitur_pendukung')]
    values['TARGET_TREATMENT_TABLE'] = table(
        ['Fitur & Model', 'Perlakuan skala / kendala target', 'MAE 127 (Rp/m²)', 'MAE 122 non-Solo (Rp/m²)', 'MAE / RMSE skala ln', 'Pred. negatif'],
        [
            [
                f"{'4 fitur VIF' if r['fitur'] == '4_fitur_vif' else '7 fitur'}: {r['keluarga_model']}",
                r['perlakuan_target'],
                rupiah(r['MAE_127_Rp']),
                rupiah(r['MAE_122_Rp']),
                (f"{decimal_id(r['MAE_skala_ln'], 3)} / {decimal_id(r['RMSE_skala_ln'], 3)}"
                 if r['MAE_skala_ln'] and r['MAE_skala_ln'] != 'nan' else 'Skala asli Rp/m²'),
                f"{r['prediksi_negatif']}/127",
            ]
            for r in retrans_4f7f
        ],
    )

    fair_subset = [r for r in fair_rows if r['skenario'] != '2 fitur utama (linear setara)']
    values['FAIR_BENCHMARK_TABLE'] = table(
        ['Skenario protokol setara', 'Model (grid kandidat)', 'MAE 127 (Rp/m²)', 'RMSE 127 (Rp/m²)', 'MAE 122 / Solo (Rp/m²)', 'R² 127 (Neg.)'],
        [
            [
                r['skenario'],
                f"{r['model']} ({r['kandidat_grid']})",
                rupiah(r['MAE_127']),
                rupiah(r['RMSE_127']),
                f"{rupiah(r['MAE_122_tanpa_solo'])} / {rupiah(r['MAE_surakarta'])}",
                f"{decimal_id(r['R2_127'], 3)} ({r['prediksi_negatif']})",
            ]
            for r in fair_subset
        ],
    )

    values['POINT_SENSITIVITY_TABLE'] = table(
        ['Representasi titik kecamatan', 'Pergeseran vs acuan (median / maks m)', 'GWR 2 fitur MAE (peringkat)', 'GWR 4 fitur Adap+R MAE (peringkat)', 'GWR 4 fitur Adap+R RMSE'],
        [
            [
                r['representasi_titik'],
                f"{decimal_id(r['median_geser_m'], 1)} / {decimal_id(r['maks_geser_m'], 1)}",
                f"{rupiah(r['GWR_2fitur_MAE'])} ({r['peringkat_GWR_2fitur']})",
                f"{rupiah(r['GWR_4fitur_Adap_MAE'])} ({r['peringkat_GWR_4fitur']})",
                rupiah(r['GWR_4fitur_Adap_RMSE']),
            ]
            for r in titik_rows
        ],
    )

    base_refs = [
        'Arafah, Y., Hanifah, W., Sabila, F., Asra, H., & Djamaluddin, M. (2026). Land Price Variation in the Urban Fringe of Banda Aceh: A Hedonic Analysis of Syiah Kuala District. The Journal of Indonesia Sustainable Development Planning, 7(2), 290–304. https://doi.org/10.46456/jisdep.v7i2.971',
        'Arumingtyas, O., Subiyanto, S., & Firdaus, H. (2019). Analisis faktor aksesibilitas, fasum dan fasos terhadap harga bidang tanah serta visualisasi berbasis WebGIS (Studi kasus: Kelurahan Tlogosari Kulon, Kecamatan Pedurungan, Kota Semarang). Jurnal Geodesi Undip, 8(4), 165–174. https://doi.org/10.14710/jgundip.2019.25155',
        'Aziz, S. (t.t.). Potensi Struktur Ruang Wilayah Polisentris. Repositori UNS, Lampiran A. Tahun publikasi perlu dikonfirmasi; 2020 merupakan tahun data. https://digilib.uns.ac.id/dokumen/download/111483/NzEwODU3/Potensi-Struktur-Ruang-Wilayah-Polisentris-Lampiran_Salim-Aziz.pdf',
        'Aziz, S., Rahayu, P., & Istanabi, T. (2023). Potensi wilayah perkotaan polisentris pada Surakarta Raya ditinjau dari perspektif pusat aktivitas. Jurnal Pengembangan Kota, 11(2), 140–154. https://doi.org/10.14710/jpk.11.2.140-154',
        'Badan Informasi Geospasial. (t.t.). Peta Wilayah Administrasi Kecamatan, KSP Satu Peta, layer 3. Metadata diperiksa ulang 17 November 2026. https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/BATAS_WILAYAH/MapServer/3',
        'Benjamini, Y., & Hochberg, Y. (1995). Controlling the False Discovery Rate: A Practical and Powerful Approach to Multiple Testing. Journal of the Royal Statistical Society: Series B, 57(1), 289–300. https://doi.org/10.1111/j.2517-6161.1995.tb02031.x',
        'Berawi, M. A., Suwartha, N., Kurnia, K., Gunawan, Miraj, P., & Berawi, A. R. B. (2018). Forecasting the Land Value around Commuter Rail Stations using Hedonic Price Modeling. International Journal of Technology, 9(7), 1329–1337. https://doi.org/10.14716/ijtech.v9i7.2589',
        'Brunsdon, C., Fotheringham, A. S., & Charlton, M. E. (1996). Geographically weighted regression: A method for exploring spatial nonstationarity. Geographical Analysis, 28(4), 281–298. https://doi.org/10.1111/j.1538-4632.1996.tb00936.x',
        'European Commission, Joint Research Centre. GHS-BUILT-S R2023A: Built-up surface grid. Kandidat sumber variabel pengembangan; belum digunakan pada hasil baseline. https://human-settlement.emergency.copernicus.eu/ghs_buS2023.php',
        'Huang, Y., & Hewings, G. (2021). More Reliable Land Price Index: Is There a Slope Effect? Land, 10(3), 261. https://doi.org/10.3390/land10030261',
        'Janssen, K. M. J., Mulder, P., & Yudhistira, M. H. (2022). Spatial sorting of rich versus poor people in Jakarta. Bulletin of Indonesian Economic Studies, 58(2), 167–194. https://doi.org/10.1080/00074918.2021.1876209',
        'Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., … Duchesnay, É. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830.',
        'Pemerintah Kota Surakarta. Laporan pada portal Dinas Lingkungan Hidup, Gambar 1.10, hlm. i-20: penduduk per kecamatan tahun 2020, sumber BPS Kota Surakarta 2021. Diakses 17 November 2026. https://dlh.surakarta.go.id/web/file/20220714104304.pdf',
        'Roberts, D. R., Bahn, V., Ciuti, S., Boyce, M. S., Elith, J., Guillera-Arroita, G., … Dormann, C. F. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or phylogenetic structure. Ecography, 40(8), 913–929. https://doi.org/10.1111/ecog.02881',
        'Saefuddin, A., Widyaningsih, Y., Ginting, A., & Mamat, M. (2012). Land price model considering spatial factors. Asian Journal of Mathematics & Statistics, 5, 132–141. https://doi.org/10.3923/ajms.2012.132.141',
        'Syahar, F., Ramadhan, R., & Putri, S. (2020). Statistical interpretation of land value patterns in Padang, Indonesia. International Journal of GEOMATE, 19(72), 109–116. https://geomatejournal.com/geomate/article/view/1136',
        'Zhang, P., Hu, S., Li, W., Zhang, C., Yang, S., & Qu, S. (2021). Modeling fine-scale residential land price distribution: An experimental study using open data and machine learning. Applied Geography, article 102442. https://doi.org/10.1016/j.apgeog.2021.102442',
    ]
    extra_refs = [
        'Anselin, L. (1995). Local Indicators of Spatial Association—LISA. Geographical Analysis, 27(2), 93–115. https://doi.org/10.1111/j.1538-4632.1995.tb00338.x',
        'Duan, N. (1983). Smearing Estimate: A Nonparametric Retransformation Method. Journal of the American Statistical Association, 78(383), 605–610. https://doi.org/10.1080/01621459.1983.10478017',
        'Jarvis, A., Reuter, H. I., Nelson, A., & Guevara, E. (2008). Hole-filled seamless SRTM data V4. CIAT. https://srtm.csi.cgiar.org/srtmdata/',
        'Meyer, H., & Pebesma, E. (2021). Predicting into unknown space? Estimating the area of applicability of spatial prediction models. Methods in Ecology and Evolution, 12(9), 1620–1633. https://doi.org/10.1111/2041-210X.13650',
        'OpenStreetMap contributors. Ekstrak Indonesia, Geofabrik, 1 Januari 2021. https://download.geofabrik.de/asia/indonesia-210101-free.shp.zip',
        'Riswandha, Y., & Wahyono, H. (2017). Pengaruh kegiatan wisata terhadap perubahan penggunaan lahan di Kecamatan Tawangmangu, Kabupaten Karanganyar. Teknik PWK, 6(2), 131–141. https://doi.org/10.14710/tpwk.2017.18052',
        'Silva, J. M. C. S., & Tenreyro, S. (2006). The Log of Gravity. The Review of Economics and Statistics, 88(4), 641–658. https://doi.org/10.1162/rest.88.4.641',
        'Wang, B. (2023). The Effect of Proximity to Universities on House Prices after the COVID Outbreak. Journal of Risk and Financial Management, 16(3), 167. https://doi.org/10.3390/jrfm16030167',
        'Wheeler, D. C. (2007). Diagnostic Tools and a Remedial Method for Collinearity in Geographically Weighted Regression. Environment and Planning A, 39, 2464–2481. https://doi.org/10.1068/a38325',
        'Zanaga, D., Van De Kerchove, R., De Keersmaecker, W., Souverijns, N., Brockmann, C., Quast, R., Wevers, J., Grosu, A., Paccini, A., Vergnaud, S., Cartus, O., Santoro, M., Fritz, S., Georgieva, I., Lesiv, M., Carter, S., Herold, M., Li, L., Tsendbazar, N. E., Ramoino, F., & Arino, O. (2021). ESA WorldCover 10 m 2020 v100 [Data set]. Zenodo. https://doi.org/10.5281/zenodo.5571936',
    ]
    all_refs = sorted(dict.fromkeys(base_refs + extra_refs), key=lambda entry: entry.casefold())
    values['REFERENCES'] = '\n\n'.join(all_refs)

    manuscript = (ROOT / 'docs/template/naskah.md').read_text(encoding='utf-8')
    for key, value in values.items():
        manuscript = manuscript.replace('{{' + key + '}}', value)
    if '{{' in manuscript:
        raise ValueError('Ada placeholder yang belum diisi.')

    markdown = ROOT / 'docs/harga_tanah_solo_raya_2020.md'
    markdown.write_text(manuscript, encoding='utf-8')
    render(ROOT / 'docs/template/sampul_naskah.docx', markdown,
           ROOT / 'docs/harga_tanah_solo_raya_2020.docx')


if __name__ == '__main__':
    main()
