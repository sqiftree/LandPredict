"""Derive documented predictors from WorldCover 2020 and archived BIG boundaries."""
import argparse,csv,hashlib,json,math,sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import numpy as np
import rasterio
import shapely,pyproj
from rasterio.features import geometry_mask
from rasterio.windows import from_bounds
from pyproj import Transformer,Geod
from shapely.geometry import shape,mapping,box
from shapely.ops import transform,unary_union

ROOT=Path(__file__).resolve().parents[1]
CLASSES={10:'tree',20:'shrub',30:'grass',40:'cropland',50:'built',60:'bare',70:'snow',80:'water',90:'wetland',95:'mangrove',100:'moss'}
URL='https://esa-worldcover.s3.eu-central-1.amazonaws.com/v100/2020/map/ESA_WorldCover_10m_2020_v100_{}_Map.tif'

def read_csv(p):
 with p.open() as f:return list(csv.DictReader(f))
def norm(s):return ' '.join(s.lower().split()).removeprefix('kabupaten ').removeprefix('kota ')
def digest(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def weighted_classes(values,inside,row_weights):
 weights=np.broadcast_to(row_weights[:,None],values.shape)
 selected=float(weights[inside].sum())
 known=inside & np.isin(values,list(CLASSES))
 valid=float(weights[known].sum())
 unknown=inside & (values!=0) & ~np.isin(values,list(CLASSES))
 if unknown.any():raise ValueError('Unknown WorldCover class')
 return selected,valid,{c:float(weights[inside & (values==c)].sum()) for c in CLASSES}
def ranks(x):
 ordered=sorted(range(len(x)),key=lambda i:x[i]);r=np.zeros(len(x));i=0
 while i<len(x):
  j=i+1
  while j<len(x) and x[ordered[j]]==x[ordered[i]]:j+=1
  r[ordered[i:j]]=(i+j-1)/2+1;i=j
 return r

def main():
 p=argparse.ArgumentParser();p.add_argument('--tiles',type=Path,required=True);args=p.parse_args()
 out=ROOT/'data/processed';out.mkdir(exist_ok=True)
 rows=read_csv(ROOT/'data/harga_tanah_2020.csv');names={(norm(r['kab_kota']),norm(r['kecamatan'])):r for r in rows}
 aliases={(norm(r['kab_sumber']),norm(r['kec_sumber'])):(norm(r['kab_kota']),norm(r['kecamatan'])) for r in read_csv(ROOT/'data/padanan_nama.csv')}
 groups=defaultdict(list)
 for f in json.loads((ROOT/'data/jawa_tengah_big.geojson').read_text())['features']:
  a=f['properties'];key=(norm(a['wadmkk']),norm(a['wadmkc']));key=aliases.get(key,key)
  if key in names:groups[key].append(shape(f['geometry']))
 assert len(groups)==len(names)==127
 to_m=Transformer.from_crs(4326,32749,always_xy=True).transform
 to_geo=Transformer.from_crs(32749,4326,always_xy=True).transform
 geod=Geod(ellps='WGS84');tiles=[];sources=[]
 for tile in ['S09E108','S09E111']:
  path=args.tiles/(tile+'.tif')
  recorded=out/'manifest.json'
  if recorded.exists():
   expected={r['tile']:r['sha256'] for r in json.loads(recorded.read_text())['sources']}
   if tile not in expected or digest(path)!=expected[tile]:raise ValueError(f'Tile hash differs from archived manifest: {tile}')
  ds=rasterio.open(path)
  assert ds.crs.to_epsg()==4326 and ds.count==1 and ds.nodata==0
  tiles.append(ds);sources.append({'tile':tile,'url':URL.format(tile),'sha256':digest(path),'bytes':path.stat().st_size,'crs':str(ds.crs),'resolution_degrees':list(ds.res),'nodata':ds.nodata})
 features=[];results=[]
 for key,row in names.items():
  geom=unary_union(groups[key]);assert geom.is_valid and not geom.is_empty
  metric=transform(to_m,geom);area=metric.area/1e6
  selected=valid=0.;counts={c:0. for c in CLASSES}
  for ds in tiles:
   clipped=geom.intersection(box(*ds.bounds))
   if clipped.is_empty or clipped.area==0:continue
   w=from_bounds(*clipped.bounds,transform=ds.transform)
   c0=max(0,math.floor(w.col_off));r0=max(0,math.floor(w.row_off));c1=min(ds.width,math.ceil(w.col_off+w.width));r1=min(ds.height,math.ceil(w.row_off+w.height))
   win=rasterio.windows.Window(c0,r0,c1-c0,r1-r0);arr=ds.read(1,window=win);aff=ds.window_transform(win)
   inside=geometry_mask([mapping(clipped)],arr.shape,aff,invert=True,all_touched=False)
   pixel_areas=[]
   for r in range(arr.shape[0]):
    x,y=aff*(0,r);dx=aff.a;dy=aff.e
    a,_=geod.polygon_area_perimeter([x,x+dx,x+dx,x],[y,y,y+dy,y+dy]);pixel_areas.append(abs(a))
   n,v,cs=weighted_classes(arr,inside,np.array(pixel_areas));selected+=n;valid+=v
   for c in counts:counts[c]+=cs[c]
  if valid<=0 or selected<=0:raise ValueError(f'No coverage {key}')
  assert abs(sum(counts.values())-valid)<max(1e-5,valid*1e-10)
  result=dict(row);result.update({'luas_arsip_km2':area,'kepadatan_penduduk_proksi':int(row['jumlah_penduduk'])/area,'kepadatan_fasum_proksi':int(row['jumlah_fasum_regional'])/area,'worldcover_valid_pct':100*valid/selected,'raster_area_km2':selected/1e6,'built_pct':100*counts[50]/valid,'cropland_pct':100*counts[40]/valid,'tree_pct':100*counts[10]/valid,'batas_2020_terverifikasi':'false'})
  for c,name in CLASSES.items():result['wc_'+name+'_pct']=100*counts[c]/valid
  results.append(result)
  display=transform(to_geo,metric.simplify(40,preserve_topology=True))
  features.append({'type':'Feature','properties':result,'geometry':mapping(display)})
 for ds in tiles:ds.close()
 def write_csv(path,data):
  with path.open('w',newline='') as f:
   w=csv.DictWriter(f,fieldnames=list(data[0]));w.writeheader();w.writerows(data)
 write_csv(out/'variabel_pendukung_2020.csv',results)
 fields=['jumlah_penduduk','jumlah_fasum_regional','kepadatan_penduduk_proksi','kepadatan_fasum_proksi','built_pct','cropland_pct','tree_pct']
 y=np.array([float(r['harga_tanah_rata_rata_rp_m2']) for r in results]);corr=[]
 for col in fields:
  x=np.array([float(r[col]) for r in results]);corr.append({'variabel':col,'n':len(x),'pearson':float(np.corrcoef(x,y)[0,1]),'spearman':float(np.corrcoef(ranks(x),ranks(y))[0,1]),'status':'eksplorasi seluruh sampel; bukan seleksi fitur atau uji signifikansi'})
 write_csv(out/'korelasi_eksploratif.csv',corr)
 manifest={'access_date':datetime.now(ZoneInfo('Asia/Bangkok')).date().isoformat(),'product':'ESA WorldCover 2020 v100','doi':'https://doi.org/10.5281/zenodo.5571936','license':'CC BY 4.0','attribution':'© ESA WorldCover project 2020 / Contains modified Copernicus Sentinel data (2020) processed by ESA WorldCover consortium','sources':sources,'input_hashes':{str(p.relative_to(ROOT)):digest(p) for p in [ROOT/'data/harga_tanah_2020.csv',ROOT/'data/jawa_tengah_big.geojson',ROOT/'data/padanan_nama.csv']},'n':len(results),'min_valid_pct':min(r['worldcover_valid_pct'] for r in results),'method':'Pixel-center mask at native resolution; ellipsoidal pixel area weights by row; class proportions over valid classified pixels. Polygon edges approximated by pixel-center inclusion. No resampling. UTM49S polygon area only for density. Display geometry simplified 40m after statistics.','geometry_2020_verified':False,'python':sys.version,'versions':{'numpy':np.__version__,'rasterio':rasterio.__version__,'shapely':shapely.__version__,'pyproj':pyproj.__version__},'csv_sha256':digest(out/'variabel_pendukung_2020.csv')}
 (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (out/'solo_raya_display.geojson').write_text(json.dumps({'type':'FeatureCollection','features':features},separators=(',',':')))
 print(json.dumps({'n':len(results),'min_valid_pct':manifest['min_valid_pct'],'correlations':corr},indent=2))
if __name__=='__main__':main()
