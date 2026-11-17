"""Build the empirical manuscript from verified outputs, then render its DOCX."""
import csv
import json
from pathlib import Path

from render_docx import render

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


def main():
    folder = ROOT / 'hasil/spasial'
    scores = read_csv(folder / 'metrik.csv')
    folds = read_csv(folder / 'per_wilayah.csv')
    predictions = read_csv(folder / 'prediksi_uji.csv')
    audit = json.loads((folder / 'audit.json').read_text())
    diagnostics = json.loads((ROOT / 'hasil/paper/diagnostics.json').read_text())
    if audit['status'] != 'complete' or len(predictions) != 127 or len(folds) != 28:
        raise ValueError('Hasil eksperimen belum lengkap.')
    regions = sorted({row['wilayah_uji'] for row in folds})
    lookup = {(row['wilayah_uji'], row['model']): row for row in folds}
    values = {
        'REGION_COUNTS': table(['Kabupaten/kota', 'Jumlah kecamatan'],
                               [[region, lookup[region, 'GWR']['n']] for region in regions]),
        'VARIABLES': table(['Komponen', 'Kolom', 'Definisi'], [
            ['Target', 'harga_tanah_rata_rata_rp_m2', 'Harga rata-rata kecamatan 2020, Rp/m²'],
            ['Prediktor', 'jumlah_penduduk', 'Jumlah penduduk, jiwa'],
            ['Prediktor', 'jumlah_fasum_regional', 'Jumlah fasilitas umum regional'],
            ['Lokasi GWR', 'lat, lon', 'Titik representatif WGS84'],
            ['Kelompok', 'kab_kota', 'Blok validasi dan uji'],
        ]),
        'METRICS': table(['Model', 'MAE (Rp/m²)', 'RMSE (Rp/m²)', 'R²'],
                         [[row['model'], rupiah(row['MAE_Rp_m2']), rupiah(row['RMSE_Rp_m2']),
                           f"{float(row['R2']):.3f}".replace('.', ',')] for row in scores]),
        'REGIONAL_MAE': table(['Wilayah', 'n', 'Linear', 'KNN', 'Tree', 'GWR'],
                              [[region, lookup[region, 'GWR']['n'],
                                *[rupiah(lookup[region, model]['MAE_Rp_m2']) for model in MODELS]] for region in regions])
                        + '\n\nSeluruh MAE pada tabel dalam Rp/m²; n adalah jumlah kecamatan uji.',
        'PARAMETERS': table(['Wilayah uji', 'k KNN', 'Kedalaman Tree', 'Bandwidth GWR (km)'],
                            [[region, *[int(float(lookup[region, model]['parameter'])) for model in MODELS[1:]]] for region in regions]),
        'NEGATIVE_TABLE': table(['Model', 'Jumlah prediksi negatif'],
                                [[model, diagnostics['negative_predictions'][model]] for model in MODELS]),
        'MAP_FIGURE': '![Gambar 1. Harga aktual dan prediksi out-of-fold; skala warna sama, batas BIG lebih baru daripada 2020.](../artifacts/figures/peta_harga_dan_prediksi.png)',
        'SCATTER_FIGURE': '![Gambar 2. Harga aktual terhadap prediksi uji. Garis putus-putus menunjukkan prediksi tepat.](../artifacts/figures/aktual_prediksi.png)',
        'FUTURE_EXPERIMENTS': table(['Tahap', 'Spesifikasi', 'Status'], [
            ['A', 'Jumlah penduduk + fasilitas regional', 'Sudah dijalankan; hasil paper ini'],
            ['B', 'Kepadatan penduduk + fasilitas regional', 'Belum diuji'],
            ['C', 'B + akses pusat kegiatan + akses jalan + proporsi terbangun', 'Data belum lengkap; belum diuji'],
            ['D', 'Variabel C dengan alternatif titik representatif', 'Belum diuji'],
        ]),
        'CONTRIBUTIONS': table(['Anggota', 'Rencana kontribusi; konfirmasi aktual oleh tim'], [
            ['Yashif Victoriawan (L0124124)', 'Integrasi program dan reproduksi eksperimen'],
            ['[Nama anggota 2]', 'Audit sumber harga dan variabel'],
            ['[Nama anggota 3]', 'Audit geometri dan data tambahan'],
            ['[Nama anggota 4]', 'Analisis galat dan penulisan pembahasan'],
        ]),
    }
    d = diagnostics['target']
    values['DESCRIPTIVE'] = (f"Harga target minimum {rupiah(d['min'])}, median {rupiah(d['50%'])}, "
                             f"rata-rata {rupiah(d['mean'])}, dan maksimum {rupiah(d['max'])} Rp/m². "
                             'Statistik ini bersifat deskriptif dan tidak digunakan untuk memasang standardisasi pada data uji.')
    solo = 'Kota Surakarta'
    shares = diagnostics['surakarta_share_squared_error']
    values['SURAKARTA_DISCUSSION'] = (
        f"Surakarta hanya memuat lima kecamatan, tetapi memiliki MAE GWR {rupiah(lookup[solo, 'GWR']['MAE_Rp_m2'])} "
        f"dan KNN {rupiah(lookup[solo, 'KNN']['MAE_Rp_m2'])} Rp/m². "
        f"Lima kecamatan ini menyumbang sekitar {100*shares['GWR']:.1f}% jumlah kuadrat galat GWR "
        f"dan {100*shares['KNN']:.1f}% jumlah kuadrat galat KNN. "
        'Besarnya galat Surakarta membantu menjelaskan perbedaan peringkat MAE dan RMSE. '
        'Ini merupakan diagnostik setelah evaluasi; wilayah tersebut tidak dikeluarkan dari perhitungan atau digunakan untuk menyetel ulang model.')
    prior = (ROOT / 'docs/Draf Revisi Harga Tanah.md').read_text()
    values['REFERENCES'] = prior.split('## e. Referensi\n', 1)[1].split('## Kontribusi Anggota', 1)[0].strip()
    manuscript = (ROOT / 'docs/paper_template.md').read_text()
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
