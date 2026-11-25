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

    values = {
        'REGION_COUNTS': table(
            ['Kabupaten/kota', 'n', 'Rata-rata harga (Rp/m²)', 'Rentang harga (Rp/m²)',
             'Total penduduk', 'Total fasum', 'Total luas (km²)'],
            region_rows,
        ),
        'VARIABLES': table(['Komponen', 'Kolom', 'Definisi'], [
            ['Target', 'harga_tanah_rata_rata_rp_m2', 'Harga rata-rata kecamatan 2020, Rp/m²'],
            ['Prediktor', 'jumlah_penduduk', 'Jumlah penduduk, jiwa'],
            ['Prediktor', 'jumlah_fasum_regional', 'Jumlah fasilitas umum regional'],
            ['Lokasi GWR', 'lat, lon', 'Titik representatif WGS84'],
            ['Kelompok', 'kab_kota', 'Blok validasi dan uji'],
        ]),
        'DESCRIPTIVE': desc_table + '\n\n' + desc_text,
        'COORDINATE_AUDIT': coord_audit_text + '\n\n' + coord_audit_table,
        'METRICS': table(['Model', 'MAE (Rp/m²)', 'RMSE (Rp/m²)', 'R²'],
                         [[row['model'], rupiah(row['MAE_Rp_m2']), rupiah(row['RMSE_Rp_m2']),
                           f"{float(row['R2']):.3f}".replace('.', ',')] for row in scores]),
        'REGIONAL_MAE': table(['Wilayah', 'n', 'Linear', 'KNN', 'Tree', 'GWR'],
                              [[region, lookup[region, 'GWR']['n'],
                                *[rupiah(lookup[region, model]['MAE_Rp_m2']) for model in MODELS]] for region in regions])
                        + '\n\nSeluruh MAE pada tabel dalam Rp/m²; n adalah jumlah kecamatan uji.',
        'REGIONAL_RMSE': table(['Wilayah', 'n', 'Linear', 'KNN', 'Tree', 'GWR'],
                               [[region, lookup[region, 'GWR']['n'],
                                 *[rupiah(lookup[region, model]['RMSE_Rp_m2']) for model in MODELS]] for region in regions])
                         + '\n\nSeluruh RMSE pada tabel dalam Rp/m²; n adalah jumlah kecamatan uji.',
        'PARAMETERS': table(['Wilayah uji', 'k KNN', 'Kedalaman Tree', 'Bandwidth GWR (km)'],
                            [[region, *[int(float(lookup[region, model]['parameter'])) for model in MODELS[1:]]] for region in regions]),
        'NEGATIVE_TABLE': table(['Model', 'Jumlah prediksi negatif'],
                                [[model, diagnostics['negative_predictions'][model]] for model in MODELS]),
        'MAP_FIGURE': '![Gambar 1. Harga aktual dan prediksi out-of-fold; skala warna sama, batas BIG lebih baru daripada 2020.](../artifacts/figures/peta_harga_dan_prediksi.png)',
        'SCATTER_FIGURE': '![Gambar 2. Harga aktual terhadap prediksi uji. Garis putus-putus menunjukkan prediksi tepat.](../artifacts/figures/aktual_prediksi.png)',
        'CANDIDATE_SOURCES': table(['Variabel pengembangan', 'Kandidat sumber resmi', 'Catatan verifikasi & tahun data'], [
            ['Kepadatan penduduk (jiwa/km²)', 'BPS (SP2020 / Publikasi Dalam Angka) dan luas poligon UTM 49S (luas_km2)',
             'Periksa tahun tabel penduduk agar mewakili 2020 dan cocok untuk 22 kecamatan Boyolali.'],
            ['Fasilitas umum regional', 'Lampiran Aziz (tahun data 2020; tahun publikasi belum dipastikan), BPS/Podes, dan instansi penyedia',
             'Definisikan kategori fasum secara konsisten; Podes 2021 bukan data 2020 sehingga hanya dipakai jika dinyatakan sebagai pendekatan.'],
            ['Akses pusat kegiatan (km)', 'Dokumen RTRW Provinsi Jawa Tengah / RTRW Kabupaten/Kota',
             'Tetapkan pusat kegiatan secara independen tanpa memakai nilai harga tanah tertinggi pada dataset.'],
            ['Akses jalan utama (km)', 'BIG / Peta Rupabumi Indonesia (RBI) dan dinas terkait',
             'Periksa klasifikasi jalan arteri/kolektor dan tahun data jaringan jalan.'],
            ['Proporsi permukaan terbangun (%)', 'ESA WorldCover 2020 v100 (diolah) dan GHSL GHS-BUILT-S R2023A epoch 2020 (alternatif)',
             'ESA WorldCover 2020 v100 sudah diolah dan diuji pada bagian 6.3–6.6; GHSL tetap menjadi alternatif pembanding dan tidak disamakan langsung dengan luas kawasan permukiman RTRW.'],
        ]),
        'FUTURE_EXPERIMENTS': table(['Tahap', 'Spesifikasi', 'Status'], [
            ['A', 'Jumlah penduduk + fasilitas regional', 'Sudah dijalankan; hasil utama bagian 4'],
            ['B', 'Kepadatan penduduk + fasilitas regional', 'Sudah diuji secara eksploratif pada bagian 6.4 dan 6.6 (kepadatan masih proksi arsip BIG)'],
            ['C', 'B + akses pusat kegiatan + akses jalan + proporsi terbangun', 'Sebagian diuji pada bagian 6.5–6.6 (tutupan lahan, wisata, kampus, topografi); akses jalan utama dan pusat kegiatan RTRW belum diuji'],
            ['D', 'Variabel C dengan alternatif titik representatif', 'Sebagian diuji pada bagian 6.4 (koordinat kiriman vs titik interior BIG); alternatif titik pusat permukiman belum diuji'],
        ]),
        'AUDIT_STATUS': table(['Komponen', 'Status saat ini', 'Bukti di repositori / tindakan audit lanjutan'], [
            ['Konsistensi komputasional 4 model & 7 lipatan', 'Terverifikasi',
             '127 prediksi uji, 7 blok, 28 baris per_wilayah; metrik dihitung ulang oleh verifier sebelum naskah dibuat. Hasil tes terpisah dicatat pada laporan audit.'],
            ['Ketercakupan interior titik GWR (ST_PointOnSurface)', 'Terverifikasi secara geometris',
             '127/127 titik di dalam poligon BIG; jarak ke batas 383,02–4.572,15 m (padanan_dan_titik.csv).'],
            ['Padanan nama wilayah (padanan_nama.csv)', '125 otomatis + 2 eksplisit; identitas historis perlu konfirmasi',
             'Kebakkramat–Kebakramat dan Sidoharjo–Sidoarjo unik tanpa benturan kunci; ejaan Sidoarjo cocok dengan PDF lampiran halaman 2; konfirmasi identitas administratif masih diperlukan.'],
            ['Kesesuaian garis batas historis tahun 2020', 'Belum terverifikasi historis',
             'Arsip BIG memiliki penanda fitur 20230928 (layanan edisi 2022); perlu audit batas khususnya pemekaran Boyolali 2018–2019 (Gladagsari, Tamansari, Wonosamodro).'],
            ['Definisi & angka primer harga tanah 2020', '381/381 nilai cocok dengan PDF; pengukuran primer belum tervalidasi',
             'Perlu konfirmasi jenis harga (transaksi, penawaran, NJOP, atau ZNT), dan cara perataan. Dokumentasi BHUMI menyebut ZNT, tetapi arsip layer 2020, metode agregasi, dan hubungan langsungnya dengan angka Lampiran A belum terverifikasi. Ketersediaan unduhan historis belum dapat dipastikan. Empat halaman tabel PDF sudah diperiksa; 21 label halaman lama dikoreksi dalam dataset rujukan terverifikasi. Perbedaan fasum pada 7 wilayah dan penduduk pada 3 wilayah belum terselesaikan.'],
        ]),
        'CONTRIBUTIONS': table(['Anggota', 'Rencana kontribusi; konfirmasi aktual oleh tim'], [
            ['Yashif Victoriawan', 'Integrasi program dan reproduksi eksperimen'],
            ['[Nama anggota 2]', 'Audit sumber harga dan variabel'],
            ['[Nama anggota 3]', 'Audit geometri dan data tambahan'],
            ['[Nama anggota 4]', 'Analisis galat dan penulisan pembahasan'],
        ]),
    }

    source_rows = read_csv(ROOT / 'artifacts/data_audit/perbandingan_fasum.csv')
    values['SOURCE_AUDIT'] = (
        'Total fasilitas pada lampiran berbeda dari penjumlahan kategori Tabel 3 artikel Aziz dkk. (2023), '
        'hlm.149, pada seluruh tujuh wilayah. Artikel menyebut observasi peneliti 2023 dengan data 2020. '
        'Perbedaan belum dapat ditentukan sebagai salah ketik, beda versi, atau beda cakupan. CSV acuan '
        'dipertahankan agar hasil eksperimen dapat ditelusuri.\n\n'
        + table(['Wilayah', 'Fasum CSV/lampiran', 'Fasum artikel', 'Selisih CSV − artikel'],
                [[r['kab_kota'], r['fasum_csv'], r['fasum_artikel'], r['selisih_csv_minus_artikel']]
                 for r in source_rows])
        + '\n\nJumlah penduduk CSV juga berbeda dari total urban dan rural Tabel 1 artikel pada Surakarta '
        '(522.364 dibanding 576.412), Sukoharjo (911.966 dibanding 907.587), dan Karanganyar '
        '(938.808 dibanding 931.963). Empat wilayah lainnya cocok. Lima angka kecamatan Surakarta '
        'cocok dengan Gambar 1.10 laporan Pemerintah Kota Surakarta, hlm.i-20, yang mengutip BPS 2021 '
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
        f"Surakarta hanya memuat lima kecamatan, tetapi memiliki MAE GWR {rupiah(lookup[solo, 'GWR']['MAE_Rp_m2'])} "
        f"dan KNN {rupiah(lookup[solo, 'KNN']['MAE_Rp_m2'])} Rp/m². "
        f"Lima kecamatan ini menyumbang sekitar {decimal_id(100 * shares['GWR'], 1)}% jumlah kuadrat galat GWR "
        f"dan {decimal_id(100 * shares['KNN'], 1)}% jumlah kuadrat galat KNN. "
        'Besarnya galat Surakarta membantu menjelaskan perbedaan peringkat MAE dan RMSE. '
        'Ini merupakan diagnostik setelah evaluasi; wilayah tersebut tidak dikeluarkan dari perhitungan atau digunakan untuk menyetel ulang model.'
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
         for r in read_csv(review / 'metrik.csv') if r['spesifikasi'] in ('kota_wisata_medan','validasi internal')])
    values['ZERO_CLIP_SUMMARY'] = (
        f"Berbeda dari eksperimen dua prediktor pada bagian 4 yang mempertahankan nilai negatif tanpa pemotongan, "
        f"eksperimen pada bagian ini menetapkan batas bawah Rp0/m². Pemotongan terjadi pada "
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
    prior = (ROOT / 'docs/arsip/draf_revisi_harga_tanah.md').read_text(encoding='utf-8')
    base_refs = [
        line.strip()
        for line in prior.split('## e. Referensi\n', 1)[1].split('## Kontribusi Anggota', 1)[0].splitlines()
        if line.strip()
    ]
    extra_refs = [
        'Jarvis, A., Reuter, H. I., Nelson, A., & Guevara, E. (2008). Hole-filled seamless SRTM data V4. CIAT. https://srtm.csi.cgiar.org/srtmdata/',
        'OpenStreetMap contributors. Ekstrak Indonesia, Geofabrik, 1 Januari 2021. https://download.geofabrik.de/asia/indonesia-210101-free.shp.zip',
        'Riswandha, Y., & Wahyono, H. (2017). Pengaruh kegiatan wisata terhadap perubahan penggunaan lahan di Kecamatan Tawangmangu, Kabupaten Karanganyar. Teknik PWK, 6(2), 131–141. https://doi.org/10.14710/tpwk.2017.18052',
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
