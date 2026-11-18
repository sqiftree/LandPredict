"""Reject corrupted experiment artifacts on the dependency-free build path."""
import csv
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from build_manuscript import ROOT, verify_stdlib


class ManuscriptVerificationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.folder = Path(self.temp.name) / 'spasial'
        shutil.copytree(ROOT / 'hasil/spasial', self.folder)

    def test_archived_predictions_pass(self):
        verify_stdlib(self.folder)

    def test_changed_prediction_is_rejected(self):
        path = self.folder / 'prediksi_uji.csv'
        with path.open() as stream:
            rows = list(csv.DictReader(stream))
        rows[0]['GWR'] = '0'
        with path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaises(AssertionError):
            verify_stdlib(self.folder)

    def test_missing_audit_is_rejected(self):
        (self.folder / 'audit.json').unlink()
        with self.assertRaises(FileNotFoundError):
            verify_stdlib(self.folder)

    def test_held_out_region_in_training_is_rejected(self):
        path = self.folder / 'audit.json'
        audit = json.loads(path.read_text())
        entry = audit['outer_folds'][0]
        entry['train_regions'].append(entry['test_region'])
        path.write_text(json.dumps(audit))
        with self.assertRaises(AssertionError):
            verify_stdlib(self.folder)


if __name__ == '__main__':
    unittest.main()
