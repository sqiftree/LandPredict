"""Tests for scientific invariants: disjoint folds, train-only scaling, singularity."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from tanah.config import KEY, ROOT
from tanah.data import attach_coordinates, load_observations
from tanah.models import LocalSingularError, estimate
from tanah.selection import region_splits, select_parameter
from tanah.verification import verify


class ProtocolTests(unittest.TestCase):
    def test_inner_selection_never_observes_outer_test(self):
        groups = np.repeat(np.array(['a', 'b', 'c', 'd']), 4)
        x = np.arange(32).reshape(16, 2)
        y = np.arange(16, dtype=float)
        _, train, test = next(region_splits(groups))
        audit = {'singular_failures': [], 'inner_scores': []}
        calls = []

        def fake_estimate(model, parameter, fit, validation, *rest):
            self.assertFalse(set(test) & set(fit))
            self.assertFalse(set(test) & set(validation))
            self.assertFalse(set(groups[fit]) & set(groups[validation]))
            calls.append(tuple(validation))
            return np.zeros(len(validation))

        with patch('tanah.selection.estimate', side_effect=fake_estimate):
            select_parameter('KNN', [3, 7], train, groups, x, y, None, 'a', audit)
        self.assertEqual(len(calls), 6)
        self.assertEqual(set(sum((list(c) for c in calls), [])), set(train))

    def test_scaling_is_fitted_on_train_only(self):
        x = np.array([[0., 1.], [2., 4.], [4., 2.], [1e9, -1e9]])
        captured = []
        original = StandardScaler.fit

        def capture(scaler, values, *args, **kwargs):
            captured.append(values.copy())
            return original(scaler, values, *args, **kwargs)

        with patch('tanah.models.StandardScaler.fit', new=capture):
            estimate('Linear', None, np.array([0, 1, 2]), np.array([3]), x, np.arange(4.), None)
        self.assertEqual(len(captured), 1)
        np.testing.assert_array_equal(captured[0], x[:3])

    def test_singular_gwr_is_explicit(self):
        x = np.column_stack([np.arange(5.), 2 * np.arange(5.)])
        with self.assertRaises(LocalSingularError):
            estimate('GWR', 10, np.arange(4), np.array([4]), x, np.arange(5.), np.zeros((5, 5)))

    def test_reject_all_singular_candidates(self):
        audit = {'singular_failures': [], 'inner_scores': []}
        with patch('tanah.selection.estimate', side_effect=LocalSingularError('singular')):
            with self.assertRaises(LocalSingularError):
                select_parameter('GWR', [5, 10], np.arange(6), np.repeat(['a', 'b', 'c'], 2),
                                 np.zeros((6, 2)), np.arange(6.), np.zeros((6, 6)), 'held-out', audit)
        self.assertEqual(audit['status'], 'failed_all_candidates_singular')
        self.assertEqual(len(audit['singular_failures']), 6)

    def test_coordinates_cannot_silently_drop_or_replace_keys(self):
        frame = load_observations()
        coords = pd.read_csv(ROOT / 'data/koordinat.csv')
        coords.loc[0, 'kecamatan'] = 'unknown district'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'coords.csv'
            coords.to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, 'Kunci koordinat'):
                attach_coordinates(frame, path)

    def test_failed_audit_prevents_verifying_stale_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)
            (path / 'audit.json').write_text(json.dumps({'status': 'failed'}))
            with self.assertRaisesRegex(AssertionError, 'CSV lama'):
                verify(path, spatial=True)

    def test_unknown_model_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Model tidak dikenal'):
            estimate('typo', None, np.arange(3), np.array([3]), np.arange(8.).reshape(4, 2), np.arange(4.), None)


if __name__ == '__main__':
    unittest.main()
