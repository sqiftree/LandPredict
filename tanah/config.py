"""Kontrak dataset dan konfigurasi eksperimen yang direproduksi."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
KEY = ["kab_kota", "kecamatan"]
TARGET = "harga_tanah_rata_rata_rp_m2"
FEATURES = ["jumlah_penduduk", "jumlah_fasum_regional"]


BASELINE_MAE = {"Linear": 739020, "KNN": 732073, "Decision Tree": 756462}
CANDIDATES = {"Linear": [None], "KNN": [3, 7, 15], "Decision Tree": [2, 4, 6], "GWR": [5, 10, 20, 40]}
