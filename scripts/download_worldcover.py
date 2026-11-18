"""Download the exact two official tiles listed in the processing manifest."""
import argparse,hashlib,json,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def sha(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'data/raw/worldcover');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 for source in json.loads((ROOT/'data/processed/manifest.json').read_text())['sources']:
  dest=a.output/(source['tile']+'.tif')
  if dest.exists() and sha(dest)==source['sha256']:print('Verified',dest);continue
  temp=dest.with_suffix('.partial')
  with urllib.request.urlopen(source['url'],timeout=120) as r,temp.open('wb') as f:
   while b:=r.read(1024*1024):f.write(b)
  if sha(temp)!=source['sha256']:raise ValueError(f'Source hash changed: {source["tile"]}; review before use')
  temp.replace(dest);print('Downloaded and verified',dest)
if __name__=='__main__':main()
