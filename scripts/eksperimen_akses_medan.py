"""Uji ablasi tujuh blok luar dengan validasi regional bersarang dan GWR ridge."""
import argparse
import csv
import hashlib
import json
import platform
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import sklearn
from sklearn.tree import DecisionTreeRegressor

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tanah.colab_models import KNNRegressorScratch, haversine_km
from tanah.config import TARGET

BASE = ['kepadatan_penduduk_proksi','kepadatan_fasum_proksi','built_pct','tree_pct',
        'cropland_pct','jumlah_penduduk','jumlah_fasum_regional']
TERRAIN = ['elevasi_median_m','lereng_median_derajat']
ACCESS = ['jarak_wisata_km','jarak_kampus_km']
SPECS = {'dasar':BASE, 'medan':BASE+TERRAIN, 'wisata':BASE+ACCESS[:1],
         'kampus':BASE+ACCESS[1:], 'akses':BASE+ACCESS, 'gabungan':BASE+TERRAIN+ACCESS,
         'dasar_log1p':BASE, 'gabungan_log1p':BASE+TERRAIN+ACCESS}
RIDGE = [.01,.1,1.]
GRID = {'Ridge global':[('global',0,a) for a in RIDGE],
        'GWR ridge':[(kind,h,a) for kind,h in [('km',15),('km',40),('adaptif',12),('adaptif',32),('adaptif',64)] for a in RIDGE],
        'KNN':[('k',k,0) for k in [3,5,7,15]],
        'Pohon':[('depth',depth,0) for depth in [2,4,6]]}
FIELDS = ['kab_kota','kecamatan']


def read(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


def by_key(path):
    rows = read(path)
    index = {tuple(r[k] for k in FIELDS):r for r in rows}
    if len(index)!=127 or len(rows)!=127:
        raise ValueError(f'Kunci duplikat atau tidak lengkap: {path}')
    return index


def save(path, rows):
    with path.open('w',newline='') as stream:
        w=csv.DictWriter(stream,fieldnames=rows[0])
        w.writeheader()
        w.writerows(rows)


def split(groups, indices):
    for name in np.unique(groups[indices]):
        test = groups[indices] == name
        yield name, indices[~test], indices[test]


def predict(x, y, dist, train, test, param):
    kind, h, penalty = param
    mean, sd = x[train].mean(axis=0), x[train].std(axis=0)
    sd[sd==0] = 1.
    xt, xv = (x[train]-mean)/sd, (x[test]-mean)/sd
    yt = np.log(y[train])
    if kind == 'k':
        return np.exp(KNNRegressorScratch(k=h).fit(xt,yt).predict(xv)), {}
    if kind == 'depth':
        tree = DecisionTreeRegressor(max_depth=h,min_samples_leaf=3,random_state=124)
        return np.exp(tree.fit(xt,yt).predict(xv)), {}
    d = dist[np.ix_(test, train)]
    if kind == 'global':
        w = np.ones_like(d)
    else:
        bw = np.partition(d,h-1,axis=1)[:,h-1,None] if kind=='adaptif' else h
        logw = -.5*(d/bw)**2
        w = np.exp(logw-logw.max(axis=1,keepdims=True))
    w /= w.sum(axis=1,keepdims=True)
    # Weighted centering leaves the intercept unpenalized. Sum of weights is one
    # so the same ridge parameter has the same scale across target locations.
    mx, my = w@xt, w@yt
    xc = xt[None,:,:]-mx[:,None,:]
    gram = xc.transpose(0,2,1) @ (w[:,:,None]*xc)
    rhs = (xc.transpose(0,2,1) @ (w*(yt-my[:,None]))[:,:,None])
    regularized = gram + penalty*np.eye(xt.shape[1])
    coef = np.linalg.solve(regularized,rhs)[:,:,0]
    pred = np.exp(my + np.sum((xv-mx)*coef,axis=1))
    return pred, {'n_efektif_min':float(np.min(1/np.sum(w*w,axis=1))),
                  'kondisi_setelah_ridge_maks':float(np.max(np.linalg.cond(regularized)))}


def metrics(actual,pred):
    err=pred-actual
    return dict(MAE_Rp_m2=float(np.mean(abs(err))), RMSE_Rp_m2=float(np.sqrt(np.mean(err**2))),
                R2=float(1-np.sum(err**2)/np.sum((actual-actual.mean())**2)))


def main(out):
    paths = [ROOT/'data/processed/variabel_pendukung_2020.csv',ROOT/'data/processed/akses_medan/fitur.csv',
             ROOT/'data/koordinat.csv']
    base, extra, coords = map(by_key,paths)
    if not base.keys()==extra.keys()==coords.keys():
        raise ValueError('Kunci berbeda.')
    keys=list(base)
    groups=np.array([k[0] for k in keys])
    idx=np.arange(len(keys))
    y=np.array([float(base[k][TARGET]) for k in keys])
    lat,lon=np.array([[float(coords[k][n]) for n in ['lat','lon']] for k in keys]).T
    dist=haversine_km(lat,lon,lat,lon)
    scores, folds, predictions, inner=[],[],[],[]
    for spec, features in SPECS.items():
        x=np.array([[float((base[k] | extra[k])[col]) for col in features] for k in keys])
        if not np.isfinite(x).all() or len(set(groups))!=7 or np.any(y<=0):
            raise ValueError('Input tidak valid.')
        if spec.endswith("_log1p"):
            if (x < 0).any():
                raise ValueError("Prediktor log1p harus nonnegatif.")
            x = np.log1p(x)
        for model, grid in GRID.items():
            oof=np.full(len(y),np.nan)
            for region, train, test in split(groups,idx):
                losses=[]
                for param in grid:
                    errors=[]
                    for _, fit, val in split(groups,train):
                        pred,_=predict(x,y,dist,fit,val,param)
                        errors.extend(abs(y[val]-pred))
                    loss=float(np.mean(errors))
                    if len(errors)!=len(train) or not np.isfinite(loss):
                        raise ValueError('Validasi internal tidak lengkap.')
                    losses.append(loss)
                    inner.append(dict(spesifikasi=spec,model=model,wilayah_luar=region,
                                      parameter=json.dumps(param),mae_internal=loss))
                best=grid[int(np.argmin(losses))]
                pred,diag=predict(x,y,dist,train,test,best)
                oof[test]=pred
                folds.append(dict(spesifikasi=spec,model=model,wilayah_uji=region,n=len(test),
                    parameter=json.dumps(best),n_efektif_min=diag.get('n_efektif_min',''),
                    kondisi_setelah_ridge_maks=diag.get('kondisi_setelah_ridge_maks',''),**metrics(y[test],pred)))
            if not np.isfinite(oof).all():
                raise ValueError('Prediksi luar tidak lengkap.')
            scores.append(dict(spesifikasi=spec,model=model,n=len(y),**metrics(y,oof)))
            for key,actual,pred in zip(keys,y,oof):
                predictions.append(dict(spesifikasi=spec,model=model,kab_kota=key[0],kecamatan=key[1],
                    aktual=actual,prediksi=pred,galat_absolut=abs(pred-actual)))
    out.mkdir(parents=True,exist_ok=True)
    for name,rows in [('prediksi_uji',predictions),('metrik',scores),('per_wilayah',folds),('seleksi_internal',inner)]:
        save(out/(name+'.csv'),rows)
    # Recompute pooled and per-block scores from serialized, keyed predictions.
    predrows=read(out/'prediksi_uji.csv')
    for row in read(out/'metrik.csv')+read(out/'per_wilayah.csv'):
        block=[r for r in predrows if (r['model'],r['spesifikasi'])==(row['model'],row['spesifikasi'])
               and r['kab_kota']==row.get('wilayah_uji',r['kab_kota'])]
        expected=[k for k in keys if k[0]==row.get('wilayah_uji',k[0])]
        if Counter((r['kab_kota'],r['kecamatan']) for r in block)!=Counter(expected):
            raise ValueError('Identitas prediksi tidak sesuai.')
        actual=np.array([float(base[r['kab_kota'],r['kecamatan']][TARGET]) for r in block])
        np.testing.assert_array_equal(actual,[float(r['aktual']) for r in block])
        for name,val in metrics(actual,np.array([float(r['prediksi']) for r in block])).items():
            np.testing.assert_allclose(val,float(row[name]),rtol=1e-10)
    audit=dict(n_kunci=len(keys),wilayah=sorted(set(groups)),jumlah_baris_wilayah=len(folds),
               fitur=SPECS,grid=GRID,seleksi='MAE gabungan enam blok validasi dalam',python=platform.python_version(),
               numpy=np.__version__,sklearn=sklearn.__version__,
               sha256={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    (out/'audit.json').write_text(json.dumps(audit,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'hasil/akses_medan')
    main(p.parse_args().output)
