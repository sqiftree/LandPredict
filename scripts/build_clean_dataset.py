"""Gabungkan dan bersihkan 3 dataset CSV LandPredict Solo Raya 2020.

Menggabungkan:
1. data/harga_tanah_2020.csv (target & fitur dasar)
2. data/processed/variabel_pendukung_2020.csv (fitur spasial & tutupan lahan ESA WorldCover 2020)
3. data/koordinat.csv (koordinat interior terverifikasi BIG KSP Satu Peta)

Menghasilkan:
- data/processed/dataset_solo_raya_2020_bersih.csv (127 baris x 18 kolom bersih)
"""

from __future__ import annotations

from pathlib import Path
import sys

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parent.parent

PATH_HARGA = ROOT / "data" / "harga_tanah_2020.csv"
PATH_PENDUKUNG = ROOT / "data" / "processed" / "variabel_pendukung_2020.csv"
PATH_KOORDINAT = ROOT / "data" / "koordinat.csv"
PATH_OUTPUT = ROOT / "data" / "processed" / "dataset_solo_raya_2020_bersih.csv"

KEY_COLS = ["kab_kota", "kecamatan"]

KOLOM_BERSIH = [
    # Kunci wilayah
    "kab_kota",
    "kecamatan",
    # Koordinat terverifikasi BIG (ST_PointOnSurface UTM 49S -> WGS84)
    "lat",
    "lon",
    # Variabel target (Rp/m2)
    "harga_tanah_rata_rata_rp_m2",
    # 7 prediktor inti
    "jumlah_penduduk",
    "jumlah_fasum_regional",
    "kepadatan_penduduk_proksi",
    "kepadatan_fasum_proksi",
    "built_pct",
    "cropland_pct",
    "tree_pct",
    # 6 prediktor tambahan non-nol (untuk inspeksi EDA)
    "luas_arsip_km2",
    "wc_shrub_pct",
    "wc_grass_pct",
    "wc_bare_pct",
    "wc_water_pct",
    "wc_wetland_pct",
]

KOLOM_DIHAPUS = {
    "duplikat_join": [
        "tahun",
        "halaman_lampiran",
        "jumlah_fasum_regional",
        "jumlah_penduduk",
        "harga_tanah_rata_rata_rp_m2",
    ],
    "metadata_administratif": [
        "tahun",
        "halaman_lampiran",
        "worldcover_valid_pct",
        "batas_2020_terverifikasi",
    ],
    "duplikat_tutupan_lahan": [
        "wc_built_pct",
        "wc_cropland_pct",
        "wc_tree_pct",
    ],
    "luas_redundan": [
        "raster_area_km2",
    ],
    "konstan_nol": [
        "wc_snow_pct",
        "wc_mangrove_pct",
        "wc_moss_pct",
    ],
}


def build_clean_dataset(
    path_harga: Path = PATH_HARGA,
    path_pendukung: Path = PATH_PENDUKUNG,
    path_koordinat: Path = PATH_KOORDINAT,
    path_output: Path = PATH_OUTPUT,
) -> pd.DataFrame:
    df_harga = pd.read_csv(path_harga)
    df_pendukung = pd.read_csv(path_pendukung)
    df_koordinat = pd.read_csv(path_koordinat)

    # 1. Validasi integritas kunci masing-masing sumber sebelum join
    for nama, df in [
        ("harga_tanah_2020.csv", df_harga),
        ("variabel_pendukung_2020.csv", df_pendukung),
        ("koordinat.csv", df_koordinat),
    ]:
        if len(df) != 127:
            raise AssertionError(f"{nama}: jumlah baris {len(df)} != 127")
        if df.isna().any().any():
            raise AssertionError(f"{nama}: mengandung nilai NaN")
        if df.duplicated(subset=KEY_COLS).any():
            raise AssertionError(f"{nama}: mengandung duplikat kunci (kab_kota, kecamatan)")

    # 2. Verifikasi nilai kolom bersama antara harga_tanah dan variabel_pendukung
    shared_cols = [
        "tahun",
        "jumlah_fasum_regional",
        "jumlah_penduduk",
        "harga_tanah_rata_rata_rp_m2",
        "halaman_lampiran",
    ]
    merged_check = df_harga.merge(
        df_pendukung, on=KEY_COLS, how="inner", suffixes=("_h", "_p")
    )
    if len(merged_check) != 127:
        raise AssertionError(f"Inner join menghasilkan {len(merged_check)} baris, bukan 127")
    for col in shared_cols:
        if not (merged_check[f"{col}_h"] == merged_check[f"{col}_p"]).all():
            raise AssertionError(f"Ketidakcocokan nilai kolom bersama '{col}' antara harga & pendukung")

    # 3. Verifikasi kolom yang akan dihapus memang duplikat / konstan / metadata
    if not (df_pendukung["wc_built_pct"] == df_pendukung["built_pct"]).all():
        raise AssertionError("wc_built_pct tidak identik dengan built_pct")
    if not (df_pendukung["wc_cropland_pct"] == df_pendukung["cropland_pct"]).all():
        raise AssertionError("wc_cropland_pct tidak identik dengan cropland_pct")
    if not (df_pendukung["wc_tree_pct"] == df_pendukung["tree_pct"]).all():
        raise AssertionError("wc_tree_pct tidak identik dengan tree_pct")
    for zero_col in KOLOM_DIHAPUS["konstan_nol"]:
        if not (df_pendukung[zero_col] == 0.0).all():
            raise AssertionError(f"Kolom {zero_col} tidak bernilai konstan nol")

    # 4. Inner-join 3 dataset tanpa duplikasi kolom dari variabel_pendukung
    pendukung_unique_cols = [
        c for c in df_pendukung.columns
        if c in KEY_COLS or c not in df_harga.columns
    ]
    df_merged = (
        df_harga
        .merge(df_koordinat, on=KEY_COLS, how="inner", validate="one_to_one")
        .merge(df_pendukung[pendukung_unique_cols], on=KEY_COLS, how="inner", validate="one_to_one")
    )

    # Pertahankan urutan baris identik dengan data/harga_tanah_2020.csv
    order_map = {
        (row.kab_kota, row.kecamatan): idx
        for idx, row in enumerate(df_harga.itertuples(index=False))
    }
    df_merged["_row_order"] = [
        order_map[(k, c)] for k, c in zip(df_merged["kab_kota"], df_merged["kecamatan"])
    ]
    df_merged = df_merged.sort_values("_row_order").drop(columns=["_row_order"]).reset_index(drop=True)

    # 5. Seleksi 18 kolom bersih sesuai kontrak skema
    df_clean = df_merged[KOLOM_BERSIH].copy()

    # 6. Asersi akhir: dimensi, 0 NaN, kunci unik, urutan baris, dan paritas nilai eksak sel-demi-sel
    assert df_clean.shape == (127, 18), f"Bentuk output tidak sesuai: {df_clean.shape}"
    assert not df_clean.isna().any().any(), "Output mengandung NaN"
    assert not df_clean.duplicated(subset=KEY_COLS).any(), "Output mengandung kunci ganda"
    assert list(zip(df_clean["kab_kota"], df_clean["kecamatan"])) == list(
        zip(df_harga["kab_kota"], df_harga["kecamatan"])
    ), "Urutan (kab_kota, kecamatan) tidak identik dengan harga_tanah_2020.csv"

    # Paritas sel-demi-sel terhadap masing-masing CSV sumber (berdasar kunci)
    h_idx = df_harga.set_index(KEY_COLS)
    p_idx = df_pendukung.set_index(KEY_COLS)
    k_idx = df_koordinat.set_index(KEY_COLS)
    c_idx = df_clean.set_index(KEY_COLS)

    for col in ["harga_tanah_rata_rata_rp_m2", "jumlah_penduduk", "jumlah_fasum_regional"]:
        assert (c_idx[col] == h_idx.loc[c_idx.index, col]).all(), f"Ketidakcocokan paritas pada {col} (harga)"
    for col in ["lat", "lon"]:
        assert np.array_equal(
            c_idx[col].to_numpy(dtype=float),
            k_idx.loc[c_idx.index, col].to_numpy(dtype=float),
        ), f"Ketidakcocokan paritas pada {col} (koordinat)"
    for col in [
        "kepadatan_penduduk_proksi",
        "kepadatan_fasum_proksi",
        "built_pct",
        "cropland_pct",
        "tree_pct",
        "luas_arsip_km2",
        "wc_shrub_pct",
        "wc_grass_pct",
        "wc_bare_pct",
        "wc_water_pct",
        "wc_wetland_pct",
    ]:
        assert np.array_equal(
            c_idx[col].to_numpy(dtype=float),
            p_idx.loc[c_idx.index, col].to_numpy(dtype=float),
        ), f"Ketidakcocokan paritas pada {col} (pendukung)"

    path_output.parent.mkdir(parents=True, exist_ok=True)
    df_clean.to_csv(path_output, index=False)

    # Verifikasi ulang hasil baca CSV dari disk
    df_reloaded = pd.read_csv(path_output)
    assert df_reloaded.shape == (127, 18)
    assert not df_reloaded.isna().any().any()

    return df_clean


def main() -> int:
    df_clean = build_clean_dataset()
    print(f"[OK] Dataset bersih tersimpan di: {PATH_OUTPUT.relative_to(ROOT)}")
    print(f"     Dimensi: {df_clean.shape[0]} baris x {df_clean.shape[1]} kolom")
    print(f"     Nilai hilang (NaN): {int(df_clean.isna().sum().sum())}")
    print(f"     Kunci unik (kab_kota, kecamatan): {df_clean[KEY_COLS].drop_duplicates().shape[0]}")
    print("     Kolom dipertahankan (18):", ", ".join(df_clean.columns))
    return 0


if __name__ == "__main__":
    sys.exit(main())
