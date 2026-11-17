"""Audit reports must not claim success after a failed source check."""
import contextlib
import csv
import io
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from scripts.audit_dataset import main, ROOT


class DatasetAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in ['data/harga_tanah_2020.csv', 'data/sumber/lampiran_a_pdf.csv',
                     'data/sumber/lampiran_a_pdf_manifest.json']:
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / name, path)

    def result(self):
        return json.loads((self.root / 'artifacts/data_audit/audit.json').read_text())

    def test_missing_pdf_is_not_reported_as_checked(self):
        with contextlib.redirect_stdout(io.StringIO()):
            main(self.root)
        result = self.result()
        self.assertFalse(result['pdf_lokal_diperiksa'])
        self.assertEqual(result['sel_cocok'], 381)
        self.assertEqual(result['rujukan_halaman_lama_berbeda'], 21)

    def test_numeric_mismatch_replaces_old_success(self):
        with contextlib.redirect_stdout(io.StringIO()):
            main(self.root)
        path = self.root / 'data/harga_tanah_2020.csv'
        with path.open() as stream:
            rows = list(csv.DictReader(stream))
        rows[0]['jumlah_penduduk'] = '1'
        with path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        with self.assertRaisesRegex(AssertionError, 'Transcription mismatch'):
            main(self.root)
        self.assertEqual(self.result()['status_kode'], 'failed')
        self.assertNotIn('sel_cocok', self.result())

    def test_changed_pdf_is_rejected(self):
        path = self.root / 'docs/Lampiran_Salim Aziz.pdf'
        path.parent.mkdir()
        path.write_bytes(b'not the audited PDF')
        with self.assertRaises(AssertionError):
            main(self.root)
        self.assertEqual(self.result()['status_kode'], 'failed')


if __name__ == '__main__':
    unittest.main()
