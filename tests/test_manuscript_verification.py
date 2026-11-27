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
        shutil.copytree(ROOT / 'artifacts/spasial', self.folder)

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

    def test_generated_manuscript_consistency(self):
        manuscript = (ROOT / 'docs/harga_tanah_solo_raya_2020.md').read_text(encoding='utf-8')
        refs = manuscript.split('## Referensi', 1)[1].split('## Lampiran', 1)[0]
        appendix = manuscript.split('## Lampiran', 1)[1]
        self.assertEqual(refs.count('Huang, Y., & Hewings, G. (2021)'), 1)
        self.assertNotIn('Huang, Y. & Hewings, G. (2021)', refs)
        self.assertIn('Zanaga, D.', refs)
        self.assertIn('Meyer, H., & Pebesma, E. (2021)', refs)
        self.assertIn('Duan, N. (1983)', refs)
        self.assertIn('Anselin, L. (1995)', refs)
        self.assertNotIn('61.7%', manuscript)
        self.assertNotIn('64.1%', manuscript)
        self.assertIn('61,7%', manuscript)
        self.assertIn('64,1%', manuscript)
        self.assertIn('19/127', manuscript)
        # Ensure team contribution table is not duplicated in appendix
        self.assertEqual(appendix.count('Yashif Victoriawan'), 1)
        self.assertNotIn('{{', manuscript)


if __name__ == '__main__':
    unittest.main()
