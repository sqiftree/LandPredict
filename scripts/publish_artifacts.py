"""Refresh reviewed result snapshots after a successful full pipeline."""
import csv
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tanah.verification import verify


def main():
    for mode in ['baseline', 'spasial']:
        verify(ROOT / 'hasil' / mode, spatial=mode == 'spasial')
    for mode in ['replikasi_notebook', 'tujuh_prediktor_big']:
        verify(ROOT / 'hasil' / mode, spatial=True, colab=True)
    analysis = ROOT / 'hasil/analisis_variabel'
    analysis_files = ['statistik_variabel.csv', 'median_per_wilayah.csv', 'korelasi_pasangan.csv',
                      *(f'{name}.{ext}' for name in ['profil_wilayah', 'sebaran_harga', 'matriks_korelasi']
                        for ext in ['png', 'pdf'])]
    for name in analysis_files:
        if not (analysis / name).is_file():
            raise FileNotFoundError(analysis / name)
    figures = ROOT / 'artifacts/figures'
    figures.mkdir(parents=True, exist_ok=True)
    required_figures = ['peta_harga_dan_prediksi.png', 'peta_harga_dan_prediksi.pdf',
                        'aktual_prediksi.png', 'aktual_prediksi.pdf', 'diagnostics.json']
    for name in required_figures:
        if not (ROOT / 'hasil/paper' / name).is_file():
            raise FileNotFoundError(f'Jalankan python -m tanah paper terlebih dahulu: {name}')
    extended_files = ['diagnostik.json', 'ablasi_knn.csv', 'evaluasi.pdf', 'evaluasi.png']
    for name in extended_files:
        if not (ROOT / 'hasil/tujuh_prediktor_big' / name).is_file():
            raise FileNotFoundError(f'Diagnostik eksperimen tujuh prediktor belum tersedia: {name}')
    access_dir = ROOT / 'hasil/akses_medan'
    access_files = ['metrik.csv', 'per_wilayah.csv', 'prediksi_uji.csv', 'seleksi_internal.csv',
                    'korelasi.csv', 'audit.json', 'akses_medan.png']
    for name in access_files:
        if not (access_dir / name).is_file():
            raise FileNotFoundError(f'Keluaran akses_medan belum tersedia: {name}')
    review_dir = ROOT / 'hasil/review_kepadatan_wisata'
    review_files = ['dataset.csv', 'korelasi.csv', 'metrik.csv', 'per_wilayah.csv',
                    'pilihan_per_wilayah.csv', 'prediksi_seleksi.csv', 'prediksi_uji.csv', 'review.json']
    for name in review_files:
        if not (review_dir / name).is_file():
            raise FileNotFoundError(f'Keluaran review_kepadatan_wisata belum tersedia: {name}')
    for mode in ['baseline', 'spasial', 'replikasi_notebook', 'tujuh_prediktor_big']:
        destination = ROOT / 'artifacts' / mode
        destination.mkdir(parents=True, exist_ok=True)
        for name in ['metrik.csv', 'per_wilayah.csv', 'prediksi_uji.csv', 'audit.json']:
            shutil.copy2(ROOT / 'hasil' / mode / name, destination / name)
    for name in required_figures:
        shutil.copy2(ROOT / 'hasil/paper' / name, figures / name)
    for name in ['dataset_paper_2020.csv', 'sha256.json']:
        shutil.copy2(ROOT / 'hasil/paper' / name, ROOT / 'artifacts' / name)
    shutil.copy2(ROOT / 'hasil/audit_spasial/padanan_dan_titik.csv', ROOT / 'artifacts/padanan_dan_titik.csv')
    shutil.copy2(ROOT / 'hasil/requirements-resolved.txt', ROOT / 'artifacts/requirements-resolved.txt')
    for name in extended_files:
        shutil.copy2(ROOT / 'hasil/tujuh_prediktor_big' / name, ROOT / 'artifacts/tujuh_prediktor_big' / name)
    access_dest = ROOT / 'artifacts/akses_medan'
    access_dest.mkdir(parents=True, exist_ok=True)
    for name in access_files:
        shutil.copy2(access_dir / name, access_dest / name)
    review_dest = ROOT / 'artifacts/review_kepadatan_wisata'
    review_dest.mkdir(parents=True, exist_ok=True)
    for name in review_files:
        shutil.copy2(review_dir / name, review_dest / name)
    with (ROOT / 'hasil/tujuh_prediktor_big/prediksi_uji.csv').open() as stream:
        predictions = [[r['kab_kota'], r['kecamatan'], float(r['KNN'])] for r in csv.DictReader(stream)]
    (ROOT / 'web/landpredict/prediksi_knn.json').write_text(json.dumps(predictions, indent=2) + '\n')
    for source, export in [('review.json', 'review.json'), ('dataset.csv', 'dataset_wisata_medan.csv'),
                           ('korelasi.csv', 'uji_korelasi.csv'), ('prediksi_seleksi.csv', 'uji_prediksi.csv')]:
        shutil.copy2(review_dir / source, ROOT / 'web/landpredict' / export)
    destination = ROOT / 'artifacts/analisis_variabel'
    destination.mkdir(parents=True, exist_ok=True)
    for name in analysis_files:
        shutil.copy2(analysis / name, destination / name)
    print('Snapshot eksperimen dan prediksi atlas diperbarui setelah verifikasi.')


if __name__ == '__main__':
    main()
