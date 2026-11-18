"""Check the portable map export before deployment, using only the standard library."""
import csv,hashlib,json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web/landpredict'
class Assets(HTMLParser):
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k not in {'src','href'} or not v:continue
   if urlsplit(v).scheme or v.startswith('#'):continue
   if v.startswith('/'):raise ValueError(f'Root-relative URL breaks project Pages: {v}')
   path=(WEB/urlsplit(v).path).resolve()
   if not path.is_relative_to(WEB.resolve()) or not path.exists():raise ValueError(f'Missing asset {v}')
def main():
 Assets().feed((WEB/'index.html').read_text())
 for name in ['variabel_pendukung_2020.csv','korelasi_eksploratif.csv','manifest.json','solo_raya_display.geojson']:
  if (WEB/name).read_bytes()!=(ROOT/'data/processed'/name).read_bytes():raise ValueError(f'Stale web export: {name}')
 manifest=json.loads((WEB/'manifest.json').read_text())
 if hashlib.sha256((WEB/'variabel_pendukung_2020.csv').read_bytes()).hexdigest()!=manifest['csv_sha256']:raise ValueError('Dataset hash mismatch')
 with (WEB/'variabel_pendukung_2020.csv').open() as f:rows=list(csv.DictReader(f))
 features=json.loads((WEB/'solo_raya_display.geojson').read_text())['features']
 keys=lambda items:{(r['kab_kota'],r['kecamatan']) for r in items}
 if len(rows)!=127 or len(features)!=127 or keys(rows)!=keys([f['properties'] for f in features]) or len(keys(rows))!=127:raise ValueError('Region keys differ')
 if list(WEB.rglob('*.pdf')) or list(WEB.rglob('*.docx')):raise ValueError('Unexpected private source documents in site export')
 print('Static export valid: relative assets, 127 regions, matching dataset hashes.')
if __name__=='__main__':main()
