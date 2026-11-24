"""Periksa ringkasan yang dicetak notebook asli terhadap CSV hasil replikasi."""
import csv
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ColabReplicationTests(unittest.TestCase):
    def test_metrics_and_bandwidths_match_saved_notebook_output(self):
        notebook = json.loads((ROOT / 'notebooks/replikasi_harga_tanah_2020.ipynb').read_text())
        output = ''.join(line for cell in notebook['cells'] for block in cell.get('outputs', [])
                         for line in block.get('text', []))
        summary = output.split('TABEL RINGKASAN EVALUASI MODEL (LEAVE-ONE-KABUPATEN-OUT)', 1)[1]
        aliases = {'OLS': 'Linear', 'DecisionTree': 'Decision Tree', 'GWR': 'GWR', 'KNN': 'KNN'}
        lines = re.findall(r'^ *(OLS|DecisionTree|GWR|KNN) +([\d.]+) +([\d.]+) +([\d.]+) +(-?[\d.]+) +0\s*$',
                           summary.split('RANKING MODEL', 1)[0], flags=re.MULTILINE)
        with (ROOT / 'artifacts/replikasi_notebook/metrik.csv').open() as stream:
            scores = {r['model']: r for r in csv.DictReader(stream)}
        self.assertEqual({row[0] for row in lines}, set(aliases))
        for name, *values in lines:
            for column, number in zip(['MAE_Rp_m2', 'RMSE_Rp_m2', 'MAPE_pct', 'R2'], values):
                self.assertAlmostEqual(float(scores[aliases[name]][column]), float(number),
                                       delta=.00005 if column == 'R2' else .005)
        expected = dict(re.findall(r'Test: (.*?) \(\d+ kec\.\) \| Bandwidth GWR Terpilih: ([\d.]+) km', output))
        with (ROOT / 'artifacts/replikasi_notebook/per_wilayah.csv').open() as stream:
            actual = {r['wilayah_uji']: float(r['parameter']) for r in csv.DictReader(stream) if r['model'] == 'GWR'}
        self.assertEqual(len(expected), 7)
        self.assertEqual(actual, {k: float(v) for k, v in expected.items()})
