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
    with (ROOT / 'hasil/tujuh_prediktor_big/prediksi_uji.csv').open() as stream:
        predictions = [[r['kab_kota'], r['kecamatan'], float(r['KNN'])] for r in csv.DictReader(stream)]
    (ROOT / 'web/landpredict/prediksi_knn.json').write_text(json.dumps(predictions, indent=2) + '\n')
    print('Snapshot eksperimen dan prediksi atlas diperbarui setelah verifikasi.')


if __name__ == '__main__':
    main()
