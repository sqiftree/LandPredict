"""Tests for advanced statistical and spatial diagnostics (tanah.rigor)."""
import unittest

import numpy as np
import pandas as pd

from tanah.config import ROOT
from tanah.rigor import (
    _load_solo_polygons,
    build_queen_weights,
    compute_aoa_loko,
    fit_predict_poisson_qmle,
    verify_rigor,
)
from tanah.sensitivity import VIF4, load_sensitivity_frame


class RigorDiagnosticsTests(unittest.TestCase):
    def test_queen_contiguity_has_no_islands_and_row_sums_to_one(self):
        frame = load_sensitivity_frame().sort_values(['kab_kota', 'kecamatan']).reset_index(drop=True)
        keys = list(frame[['kab_kota', 'kecamatan']].itertuples(index=False, name=None))
        polys = _load_solo_polygons()
        adj, w = build_queen_weights(keys, polys)
        self.assertEqual(adj.shape, (127, 127))
        np.testing.assert_allclose(adj, adj.T)
        self.assertTrue((adj.sum(axis=1) >= 1).all())
        np.testing.assert_allclose(w.sum(axis=1), np.ones(127), rtol=1e-12)

    def test_aoa_does_not_observe_test_targets(self):
        frame = load_sensitivity_frame()
        aoa_a, _ = compute_aoa_loko(frame, VIF4)
        mutated = frame.copy()
        mutated['harga_tanah_rata_rata_rp_m2'] = 1.0
        aoa_b, _ = compute_aoa_loko(mutated, VIF4)
        np.testing.assert_allclose(aoa_a['DI'], aoa_b['DI'], rtol=1e-12)
        np.testing.assert_allclose(aoa_a['ambang_AoA'], aoa_b['ambang_AoA'], rtol=1e-12)

    def test_poisson_qmle_guarantees_strictly_positive_predictions(self):
        rng = np.random.default_rng(124)
        x_tr = rng.normal(size=(40, 2))
        y_tr = np.exp(12.0 + 0.8 * x_tr[:, 0] - 0.5 * x_tr[:, 1])
        x_te = np.array([[-5.0, 5.0], [0.0, 0.0], [3.0, -2.0]])
        preds = fit_predict_poisson_qmle(x_tr, y_tr, x_te, reg_lambda=0.1)
        self.assertTrue(np.isfinite(preds).all())
        self.assertTrue((preds > 0).all())

    def test_archived_rigor_artifacts_verify(self):
        verify_rigor(ROOT / 'artifacts/diagnostik_lanjut')


if __name__ == '__main__':
    unittest.main()
