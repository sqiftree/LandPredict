"""Refresh reviewed result snapshots after a successful full pipeline."""
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tanah.verification import verify


def main():
    for mode in ['baseline', 'spasial']:
        verify(ROOT / 'hasil' / mode, spatial=mode == 'spasial')
    figures = ROOT / 'artifacts/figures'
    figures.mkdir(parents=True, exist_ok=True)
    required_figures = ['peta_harga_dan_prediksi.png', 'peta_harga_dan_prediksi.pdf',
                        'aktual_prediksi.png', 'aktual_prediksi.pdf', 'diagnostics.json']
    for name in required_figures:
        if not (ROOT / 'hasil/paper' / name).is_file():
            raise FileNotFoundError(f'Jalankan python -m tanah paper terlebih dahulu: {name}')
    for mode in ['baseline', 'spasial']:
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
    print('Snapshot artifacts diperbarui setelah verifikasi kedua eksperimen.')


if __name__ == '__main__':
    main()
