"""Reproduce coordinates, models, checks and figures from archived inputs."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMANDS = [
    ['scripts/restore_geometry.py'],
    ['-m', 'tanah', 'run', '--output', 'hasil/baseline'],
    ['-m', 'tanah', 'verify', 'hasil/baseline'],
    ['-m', 'tanah', 'coordinates', 'data/jawa_tengah_big.geojson', '--kab', 'wadmkk', '--kec', 'wadmkc',
     '--padanan', 'data/padanan_nama.csv', '--output', 'data/koordinat.csv'],
    ['-m', 'tanah', 'audit'],
    ['-m', 'tanah', 'run', '--koordinat', 'data/koordinat.csv', '--output', 'hasil/spasial'],
    ['-m', 'tanah', 'verify', 'hasil/spasial', '--spasial'],
    ['scripts/check_regression.py', 'artifacts/baseline', 'hasil/baseline'],
    ['scripts/check_regression.py', 'artifacts/spasial', 'hasil/spasial'],
    ['-m', 'tanah', 'paper'],
    ['-m', 'tanah', 'colab', '--output', 'hasil/replikasi_notebook'],
    ['-m', 'tanah', 'colab', '--koordinat', 'data/koordinat.csv', '--output', 'hasil/tujuh_prediktor_big'],
    ['scripts/check_regression.py', 'artifacts/replikasi_notebook', 'hasil/replikasi_notebook'],
    ['scripts/check_regression.py', 'artifacts/tujuh_prediktor_big', 'hasil/tujuh_prediktor_big'],
    ['scripts/diagnostik_colab.py', 'hasil/tujuh_prediktor_big'],
    ['scripts/analisis_variabel.py', 'hasil/analisis_variabel'],
    ['scripts/check_regression.py', 'artifacts/analisis_variabel', 'hasil/analisis_variabel', '--tables',
     'statistik_variabel.csv', 'median_per_wilayah.csv', 'korelasi_pasangan.csv'],
    ['scripts/eksperimen_akses_medan.py', '--output', 'hasil/akses_medan'],
    ['scripts/grafik_akses_medan.py', 'hasil/akses_medan'],
    ['scripts/check_regression.py', 'artifacts/akses_medan', 'hasil/akses_medan', '--tables',
     'metrik.csv', 'per_wilayah.csv', 'prediksi_uji.csv', 'seleksi_internal.csv', 'korelasi.csv'],
    ['scripts/review_kepadatan_wisata.py'],
    ['scripts/check_regression.py', 'artifacts/review_kepadatan_wisata', 'hasil/review_kepadatan_wisata', '--tables',
     'dataset.csv', 'korelasi.csv', 'metrik.csv', 'per_wilayah.csv', 'pilihan_per_wilayah.csv',
     'prediksi_seleksi.csv', 'prediksi_uji.csv'],
]


def main():
    for command in COMMANDS:
        print(f'>>> {sys.executable} {" ".join(command)}', flush=True)
        subprocess.run([sys.executable, *command], cwd=ROOT, check=True)


if __name__ == '__main__':
    main()
