"""Gabungkan observasi dan prediksi uji ke poligon; ekspor dataset dan gambar paper."""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.path import Path as PlotPath
from matplotlib.patches import PathPatch
import numpy as np
import pandas as pd
from pyproj import Transformer
from shapely.geometry import shape
from shapely.geometry.polygon import orient
from shapely.ops import transform

from .config import ROOT, KEY, TARGET
from .verification import verify
from .diagnostics import summarize


def main():
    verify(ROOT / 'hasil/spasial', spatial=True)
    out = ROOT / 'hasil/paper'
    out.mkdir(parents=True, exist_ok=True)
    pred = pd.read_csv(ROOT / 'hasil/spasial/prediksi_uji.csv')
    audit = pd.read_csv(ROOT / 'hasil/audit_spasial/padanan_dan_titik.csv', dtype={'kode_sumber': str})
    df = pred.merge(audit.drop(columns=['lat', 'lon']), on=KEY, validate='one_to_one')
    assert len(df) == 127 and df.di_dalam_poligon.all() and df.kode_sumber.nunique() == 127
    project = Transformer.from_crs(4326, 32749, always_xy=True)
    df['easting_utm49s_m'], df['northing_utm49s_m'] = project.transform(df.lon.to_numpy(), df.lat.to_numpy())
    df['status_batas_2020'] = 'Belum diverifikasi historis; geometri BIG metadata 2023-09-28'
    df['sumber_geometri'] = 'https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/BATAS_WILAYAH/MapServer/3'
    for model in ['Linear', 'KNN', 'Decision Tree', 'GWR']:
        df[f'residu_{model}_rp_m2'] = df[TARGET] - df[model]
    df.to_csv(out / 'dataset_paper_2020.csv', index=False)
    source = json.loads((ROOT / 'hasil/audit_spasial/solo_raya.geojson').read_text())
    lookup = {tuple(row[k] for k in KEY): row for row in json.loads(df.to_json(orient='records', double_precision=15))}
    geoms, rows = [], []
    for feature in source['features']:
        key = tuple(feature['properties'][k] for k in KEY)
        feature['properties'] = lookup[key]
        rows.append(lookup[key])
        geoms.append(transform(project.transform, shape(feature['geometry'])))
    assert len(rows) == 127 and len({tuple(r[k] for k in KEY) for r in rows}) == 127
    (out / 'harga_prediksi_solo_raya_2020.geojson').write_text(json.dumps(source, ensure_ascii=False, allow_nan=False))
    values = pd.DataFrame(rows)
    columns = [TARGET, 'Linear', 'KNN', 'Decision Tree', 'GWR']
    norm = Normalize(vmin=min(values[c].min() for c in columns) / 1e6,
                     vmax=max(values[c].max() for c in columns) / 1e6)
    fig, axes = plt.subplots(2, 3, figsize=(15, 11), layout='constrained')
    def patch(poly, color):
        poly = orient(poly)
        vertices, codes = [], []
        for ring in [poly.exterior, *poly.interiors]:
            coords = np.asarray(ring.coords) / 1000
            vertices.extend(coords)
            codes.extend([PlotPath.MOVETO] + [PlotPath.LINETO] * (len(coords)-2) + [PlotPath.CLOSEPOLY])
        return PathPatch(PlotPath(vertices, codes), facecolor=color, edgecolor='#444444', linewidth=.25)
    for ax, col in zip(axes.flat, columns):
        for geom, val in zip(geoms, values[col]):
            for poly in ([geom] if geom.geom_type == 'Polygon' else geom.geoms):
                ax.add_patch(patch(poly, plt.get_cmap('viridis')(norm(val / 1e6))))
        ax.autoscale_view()
        ax.set_aspect('equal')
        ax.set_title('Harga aktual 2020' if col == TARGET else f'Prediksi uji {col}')
        ax.set_xlabel('UTM 49S easting (km)')
        ax.set_ylabel('Northing (km)')
    axes.flat[-1].axis('off')
    axes.flat[-1].text(0, .9, '127 kecamatan; 7 blok kabupaten/kota\nPrediksi out-of-fold: seluruh kabupaten/kota\nuji dikeluarkan dari pelatihan.\n\nWarna memakai skala yang sama.\nBatas BIG metadata 2023-09-28;\nkecocokan geometri tahun 2020\nbelum dipastikan.\n\nNilai rata-rata kecamatan,\nbukan harga bidang tanah.', va='top', fontsize=11)
    fig.colorbar(ScalarMappable(norm=norm, cmap='viridis'), ax=list(axes.flat[:5]), shrink=.55, label='Juta Rp/m²')
    fig.suptitle('Harga tanah rata-rata kecamatan Solo Raya tahun 2020')
    fig.savefig(out / 'peta_harga_dan_prediksi.png', dpi=180)
    fig.savefig(out / 'peta_harga_dan_prediksi.pdf')
    plt.close(fig)
    files = ['data/harga_tanah_2020.csv', 'data/jawa_tengah_big.geojson', 'data/koordinat.csv',
             'data/padanan_nama.csv',
             'hasil/spasial/metrik.csv', 'hasil/spasial/per_wilayah.csv', 'hasil/spasial/prediksi_uji.csv']
    files.extend(str(p.relative_to(ROOT)) for p in sorted((ROOT / 'tanah').glob('*.py')))
    (out / 'sha256.json').write_text(json.dumps({p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}, indent=2))
    summarize(ROOT / 'hasil/spasial', out)
    print(f'Dataset 127 kecamatan, GeoJSON WGS84 dan peta UTM 49S: {out}')


