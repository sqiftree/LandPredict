"""Tests for GWR sensitivity module: intercept-free Ridge, adaptive kernels, no leakage."""
import unittest

import numpy as np

from tanah.config import ROOT
from tanah.selection import region_splits
from tanah.sensitivity import ALL7, VIF4, RidgeGWR, _evaluate_loro, load_sensitivity_frame, verify_sensitivity


class SensitivityTests(unittest.TestCase):
    def test_ridge_gwr_does_not_penalize_intercept(self):
        rng = np.random.default_rng(7)
        x = rng.normal(size=(25, 3))
        coords = np.column_stack([
            -7.55 + rng.uniform(-0.1, 0.1, size=25),
            110.82 + rng.uniform(-0.1, 0.1, size=25),
        ])
        y = 100.0 + 2.0 * x[:, 0] - 0.5 * x[:, 1] + rng.normal(scale=0.1, size=25)
        shift = 500000.0
        m_base = RidgeGWR(bandwidth=25.0, kernel='gaussian', adaptive=False, reg_lambda=10.0).fit(x, y, coords)
        m_shift = RidgeGWR(bandwidth=25.0, kernel='gaussian', adaptive=False, reg_lambda=10.0).fit(x, y + shift, coords)
        np.testing.assert_allclose(m_shift.predict(x[:5], coords[:5]) - m_base.predict(x[:5], coords[:5]), shift, rtol=1e-9)

    def test_adaptive_kernels_produce_finite_distinct_predictions(self):
        rng = np.random.default_rng(42)
        x = rng.normal(size=(30, 2))
        coords = np.column_stack([
            np.concatenate([np.full(15, -7.55) + rng.uniform(-0.01, 0.01, 15),
                            np.full(15, -7.85) + rng.uniform(-0.2, 0.2, 15)]),
            np.concatenate([np.full(15, 110.82) + rng.uniform(-0.01, 0.01, 15),
                            np.full(15, 110.95) + rng.uniform(-0.2, 0.2, 15)]),
        ])
        y = 10.0 + 3.0 * x[:, 0] + (coords[:, 0] + 7.55) * 5.0
        x_te, c_te = x[:6], coords[:6]
        p_fix = RidgeGWR(bandwidth=5.0, kernel='gaussian', adaptive=False, reg_lambda=0.1).fit(x[6:], y[6:], coords[6:]).predict(x_te, c_te)
        p_ad_g = RidgeGWR(bandwidth=12, kernel='gaussian', adaptive=True, reg_lambda=0.1).fit(x[6:], y[6:], coords[6:]).predict(x_te, c_te)
        p_ad_b = RidgeGWR(bandwidth=12, kernel='bisquare', adaptive=True, reg_lambda=0.1).fit(x[6:], y[6:], coords[6:]).predict(x_te, c_te)
        self.assertTrue(np.isfinite(p_fix).all() and np.isfinite(p_ad_g).all() and np.isfinite(p_ad_b).all())
        self.assertFalse(np.allclose(p_fix, p_ad_g))
        self.assertFalse(np.allclose(p_ad_g, p_ad_b))

    def test_loro_evaluation_does_not_leak_test_targets(self):
        frame = load_sensitivity_frame()
        # Corrupt one region's targets; predictions for that region must stay identical.
        mutated = frame.copy()
        solo_mask = mutated['kab_kota'] == 'Kota Surakarta'
        mutated.loc[solo_mask, 'harga_tanah_rata_rata_rp_m2'] = 1.0
        specs = [{'name': 'GWR Adap Gauss + Ridge', 'kind': 'adap_gauss', 'bws': [15, 25], 'lambdas': [0.1, 1.0], 'log_target': False}]
        pred_orig, _, _ = _evaluate_loro(frame, VIF4, specs)
        pred_mut, _, _ = _evaluate_loro(mutated, VIF4, specs)
        np.testing.assert_allclose(
            pred_orig.loc[solo_mask, 'GWR Adap Gauss + Ridge'],
            pred_mut.loc[solo_mask, 'GWR Adap Gauss + Ridge'],
            rtol=1e-12,
        )
        # Disjoint splits invariant
        groups = frame['kab_kota'].to_numpy()
        for region, train, test in region_splits(groups):
            self.assertFalse(set(train) & set(test))
            self.assertNotIn(region, set(groups[train]))

    def test_archived_sensitivity_artifacts_verify(self):
        verify_sensitivity(ROOT / 'artifacts/sensitivitas_gwr')
        self.assertEqual(len(ALL7), 7)
        self.assertEqual(len(VIF4), 4)


if __name__ == '__main__':
    unittest.main()
