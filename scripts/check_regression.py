"""Compare refactored outputs with archived pre-refactor scientific results."""
import argparse
import json
from pathlib import Path

import pandas as pd
import numpy as np


def compare_tables(expected: Path, actual: Path, tables: list[str]) -> None:
    for name in tables:
        pd.testing.assert_frame_equal(pd.read_csv(expected / name), pd.read_csv(actual / name),
                                      check_exact=False, rtol=1e-12, atol=1e-8)
    print(f'PASS: tabel konsisten ({", ".join(tables)}): {actual}')


def compare(expected: Path, actual: Path) -> None:
    for name in ['metrik.csv', 'per_wilayah.csv', 'prediksi_uji.csv']:
        pd.testing.assert_frame_equal(pd.read_csv(expected / name), pd.read_csv(actual / name),
                                      check_exact=False, rtol=1e-12, atol=1e-8)
    old = json.loads((expected / 'audit.json').read_text())
    new = json.loads((actual / 'audit.json').read_text())
    for field in ['outer_folds', 'singular_failures', 'features', 'data_sha256', 'coordinates_sha256']:
        if old[field] != new[field]:
            raise AssertionError(f'Protokol atau input berubah: {field}')
    if len(old['inner_scores']) != len(new['inner_scores']):
        raise AssertionError('Jumlah skor internal berubah.')
    if old.get('protocol') == 'colab_log7':
        for field in ['protocol', 'supporting_sha256', 'outside_BIG', 'candidate_parameters']:
            assert old[field] == new[field], field
        for a, b in zip(old['inner_scores'], new['inner_scores']):
            assert a['outer_region'] == b['outer_region'] and a['bandwidth_km'] == b['bandwidth_km']
            np.testing.assert_allclose(a['RMSE_Rp_m2'], b['RMSE_Rp_m2'], rtol=1e-12)
        print(f'PASS: replikasi protokol tujuh prediktor: {actual}')
        return
    for a, b in zip(old['inner_scores'], new['inner_scores']):
        for field in ['model', 'outer_region', 'parameter', 'valid']:
            if a[field] != b[field]:
                raise AssertionError(f'Seleksi internal berubah: {field}')
        if a['MAE_Rp_m2'] is None or b['MAE_Rp_m2'] is None:
            if a['MAE_Rp_m2'] != b['MAE_Rp_m2']:
                raise AssertionError('Status singular kandidat berubah.')
        else:
            np.testing.assert_allclose(a['MAE_Rp_m2'], b['MAE_Rp_m2'], rtol=1e-12, atol=1e-8)
    print(f'PASS: prediksi, metrik, parameter, inner scores dan fold konsisten: {actual}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('expected', type=Path)
    parser.add_argument('actual', type=Path)
    parser.add_argument('--tables', nargs='+', help='Bandingkan hanya daftar tabel CSV tertentu')
    args = parser.parse_args()
    if args.tables:
        compare_tables(args.expected, args.actual, args.tables)
    else:
        compare(args.expected, args.actual)
