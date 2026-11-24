"""Periksa struktur keluaran dan hitung ulang metrik dari prediksi uji."""
import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .config import BASELINE_MAE, KEY, ROOT, TARGET


def verify(folder, spatial=False, colab=False):
    if not __debug__:
        raise RuntimeError('Jalankan verifikasi tanpa python -O agar assertions aktif.')
    audit_path = folder / 'audit.json'
    audit = json.loads(audit_path.read_text()) if audit_path.exists() else None
    if audit is not None:
        assert audit['status'] == 'complete', 'Eksperimen gagal/belum selesai; CSV lama tidak boleh dipakai.'
    if colab:
        assert spatial and audit and audit.get("protocol") == "colab_log7"
    source = pd.read_csv(ROOT / "data/harga_tanah_2020.csv")
    predictions = pd.read_csv(folder / "prediksi_uji.csv")
    metrics = pd.read_csv(folder / "metrik.csv")
    folds = pd.read_csv(folder / "per_wilayah.csv")
    models = ["Linear", "KNN", "Decision Tree"] + (["GWR"] if spatial else [])
    assert len(source) == len(predictions) == 127, "Harus ada 127 kecamatan"
    assert not source.duplicated(KEY).any() and not predictions.duplicated(KEY).any()
    pd.testing.assert_frame_equal(
        source[KEY + [TARGET]].sort_values(KEY).reset_index(drop=True),
        predictions[KEY + [TARGET]].sort_values(KEY).reset_index(drop=True),
    )
    assert predictions.kab_kota.nunique() == 7
    pd.testing.assert_frame_equal(source.sort_values(KEY).reset_index(drop=True),
                                  predictions[source.columns].sort_values(KEY).reset_index(drop=True))
    assert len(metrics) == len(models) and set(metrics.model) == set(models)
    assert len(folds) == 7 * len(models) and set(folds.model) == set(models)
    assert not folds.duplicated(["model", "wilayah_uji"]).any()
    expected = BASELINE_MAE
    for model in models:
        assert np.isfinite(predictions[model]).all(), f"Prediksi tidak valid: {model}"
        error = predictions[TARGET] - predictions[model]
        mae, rmse = error.abs().mean(), np.sqrt(np.mean(error ** 2))
        row = metrics.set_index("model").loc[model]
        np.testing.assert_allclose([mae, rmse], row[["MAE_Rp_m2", "RMSE_Rp_m2"]].to_numpy(dtype=float), rtol=1e-10)
        r2 = 1 - np.sum(error ** 2) / np.sum((predictions[TARGET] - predictions[TARGET].mean()) ** 2)
        np.testing.assert_allclose(r2, float(row['R2']), rtol=1e-10)
        if colab:
            np.testing.assert_allclose(row["MAPE_pct"], 100 * (error.abs() / predictions[TARGET]).mean())
        elif model in expected:
            assert round(mae) == expected[model], f"MAE baseline berubah: {model}: {mae}"
        block = folds[folds.model == model].set_index("wilayah_uji")
        assert set(block.index) == set(predictions.kab_kota.unique())
        for region, group in predictions.groupby("kab_kota"):
            assert block.loc[region, "n"] == len(group)
            np.testing.assert_allclose(block.loc[region, "MAE_Rp_m2"], (group[TARGET] - group[model]).abs().mean(), rtol=1e-10)
            if "RMSE_Rp_m2" in block.columns:
                np.testing.assert_allclose(block.loc[region, "RMSE_Rp_m2"],
                    np.sqrt(np.mean((group[TARGET] - group[model]) ** 2)), rtol=1e-10)
        if audit is not None:
            entries = [entry for entry in audit['outer_folds'] if entry['model'] == model]
            assert len(entries) == 7
            assert {entry['test_region'] for entry in entries} == set(block.index)
            for entry in entries:
                held_out = entry['test_region']
                assert set(entry['train_regions']) == set(block.index) - {held_out}
                assert set(map(tuple, entry['test_keys'])) == set(map(tuple, predictions.loc[predictions.kab_kota == held_out, KEY].values))
        print(f"{model}: 127 prediksi, 7 blok; MAE {mae:,.3f}; RMSE {rmse:,.3f} Rp/m²")
    print(f"Valid: {len(folds)} baris per_wilayah.csv")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("folder", type=Path)
    parser.add_argument("--spasial", action="store_true", help="Wajibkan empat model termasuk GWR")
    parser.add_argument("--colab", action="store_true", help="Verifikasi protokol tujuh prediktor log-harga")
    args = parser.parse_args()
    verify(args.folder, args.spasial or args.colab, args.colab)
