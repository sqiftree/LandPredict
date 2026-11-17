"""Build the empirical manuscript from verified outputs, then render its DOCX."""
import csv
import json
import math
import statistics
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


def main():
    audit_dataset()
    folder = ROOT / 'hasil/spasial'
    scores = read_csv(folder / 'metrik.csv')
    folds = read_csv(folder / 'per_wilayah.csv')
    predictions = read_csv(folder / 'prediksi_uji.csv')
    dataset = read_csv(ROOT / 'hasil/paper/dataset_paper_2020.csv')
    audit = json.loads((folder / 'audit.json').read_text(encoding='utf-8'))
    diagnostics = json.loads((ROOT / 'hasil/paper/diagnostics.json').read_text(encoding='utf-8'))
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
        f"dan selisih numerik point-on-surface terhadap Shapely kurang dari {max_pos_diff:.2e} m."
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
            ['Proporsi permukaan terbangun (%)', 'European Commission JRC — GHSL GHS-BUILT-S R2023A epoch 2020 (100 m)',
             'Mengukur permukaan terbangun agregat per poligon kecamatan; tidak disamakan langsung dengan luas kawasan permukiman RTRW.'],
        ]),
        'FUTURE_EXPERIMENTS': table(['Tahap', 'Spesifikasi', 'Status'], [
            ['A', 'Jumlah penduduk + fasilitas regional', 'Sudah dijalankan; hasil paper ini'],
            ['B', 'Kepadatan penduduk + fasilitas regional', 'Belum diuji'],
            ['C', 'B + akses pusat kegiatan + akses jalan + proporsi terbangun', 'Data belum lengkap; belum diuji'],
            ['D', 'Variabel C dengan alternatif titik representatif', 'Belum diuji'],
        ]),
        'AUDIT_STATUS': table(['Komponen', 'Status saat ini', 'Bukti di repositori / tindakan audit lanjutan'], [
            ['Konsistensi komputasional 4 model & 7 lipatan', 'Terverifikasi',
             '127 prediksi uji, 7 blok, 28 baris per_wilayah, 7/7 tes protokol lulus, 25/25 hash sha256.json cocok.'],
            ['Ketercakupan interior titik GWR (ST_PointOnSurface)', 'Terverifikasi secara geometris',
             '127/127 titik di dalam poligon BIG; jarak ke batas 383,02–4.572,15 m (padanan_dan_titik.csv).'],
            ['Padanan nama wilayah (padanan_nama.csv)', '125 otomatis + 2 eksplisit; identitas historis perlu konfirmasi',
             'Kebakkramat–Kebakramat dan Sidoharjo–Sidoarjo unik tanpa benturan kunci; ejaan Sidoarjo cocok dengan indeks lampiran; konfirmasi identitas administratif masih diperlukan.'],
            ['Kesesuaian garis batas historis tahun 2020', 'Belum terverifikasi historis',
             'Arsip BIG memiliki penanda fitur 20230928 (layanan edisi 2022); perlu audit batas khususnya pemekaran Boyolali 2018–2019 (Gladagsari, Tamansari, Wonosamodro).'],
            ['Definisi & angka primer harga tanah 2020', '381/381 nilai cocok dengan indeks; primer belum tervalidasi',
             'Perlu konfirmasi jenis harga (transaksi, penawaran, NJOP, atau ZNT), cara perataan, dan pemeriksaan visual PDF asli UNS. Perbedaan fasum pada 7 wilayah dan penduduk pada 3 wilayah belum terselesaikan.'],
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

    solo = 'Kota Surakarta'
    shares = diagnostics['surakarta_share_squared_error']
    values['SURAKARTA_DISCUSSION'] = (
        f"Surakarta hanya memuat lima kecamatan, tetapi memiliki MAE GWR {rupiah(lookup[solo, 'GWR']['MAE_Rp_m2'])} "
        f"dan KNN {rupiah(lookup[solo, 'KNN']['MAE_Rp_m2'])} Rp/m². "
        f"Lima kecamatan ini menyumbang sekitar {100*shares['GWR']:.1f}% jumlah kuadrat galat GWR "
        f"dan {100*shares['KNN']:.1f}% jumlah kuadrat galat KNN. "
        'Besarnya galat Surakarta membantu menjelaskan perbedaan peringkat MAE dan RMSE. '
        'Ini merupakan diagnostik setelah evaluasi; wilayah tersebut tidak dikeluarkan dari perhitungan atau digunakan untuk menyetel ulang model.'
    )

    prior = (ROOT / 'docs/Draf Revisi Harga Tanah.md').read_text(encoding='utf-8')
    values['REFERENCES'] = prior.split('## e. Referensi\n', 1)[1].split('## Kontribusi Anggota', 1)[0].strip()

    manuscript = (ROOT / 'docs/paper_template.md').read_text(encoding='utf-8')
    for key, value in values.items():
        manuscript = manuscript.replace('{{' + key + '}}', value)
    if '{{' in manuscript:
        raise ValueError('Ada placeholder yang belum diisi.')

    markdown = ROOT / 'docs/Paper Harga Tanah Solo Raya.md'
    markdown.write_text(manuscript, encoding='utf-8')
    render(ROOT / 'docs/Draf Paper TUBES Machine Learning Harga Tanah (1).docx', markdown,
           ROOT / 'docs/Paper Harga Tanah Solo Raya.docx')


if __name__ == '__main__':
    main()
