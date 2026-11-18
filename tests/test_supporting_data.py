"""Check weighted area aggregation and published feature integrity."""
import unittest,json,csv
import numpy as np
from scripts.process_supporting_data import weighted_classes,ranks,ROOT,CLASSES

class SupportingDataTests(unittest.TestCase):
 def test_nodata_excluded_from_class_denominator(self):
  a=np.array([[50,0],[10,40]]);mask=np.ones((2,2),dtype=bool)
  total,valid,c=weighted_classes(a,mask,np.array([2.,1.]))
  self.assertEqual(total,6);self.assertEqual(valid,4);self.assertEqual(c[50]/valid,.5)
 def test_outside_pixels_never_count(self):
  a=np.array([[50,40]]);total,valid,c=weighted_classes(a,np.array([[True,False]]),np.array([3.]))
  self.assertEqual(total,3);self.assertEqual(c[40],0)
 def test_unknown_class_fails(self):
  with self.assertRaises(ValueError):weighted_classes(np.array([[255]]),np.array([[True]]),np.array([1.]))
 def test_tied_ranks(self):
  np.testing.assert_array_equal(ranks([4,1,1,2]),[4,1.5,1.5,3])
 def test_output_complete_and_finite(self):
  with (ROOT/'data/processed/variabel_pendukung_2020.csv').open() as f:rows=list(csv.DictReader(f))
  self.assertEqual(len({(r['kab_kota'],r['kecamatan']) for r in rows}),127)
  for r in rows:
   fractions=[float(r['wc_'+n+'_pct']) for n in CLASSES.values()]
   self.assertAlmostEqual(sum(fractions),100,places=8)
   self.assertTrue(all(0<=v<=100+1e-8 for v in fractions))
   self.assertGreaterEqual(float(r['worldcover_valid_pct']),99.99)
   self.assertEqual(r['batas_2020_terverifikasi'],'false')
  with (ROOT/'data/harga_tanah_2020.csv').open() as f:source=list(csv.DictReader(f))
  for a,b in zip(source,rows):
   for col in a:self.assertEqual(a[col],b[col])
if __name__=='__main__':unittest.main()
