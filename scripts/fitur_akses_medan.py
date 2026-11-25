"""Topografi SRTM dan jarak ke objek OSM historis untuk kecamatan Solo Raya."""
import csv
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from rasterio.features import geometry_mask, geometry_window
from shapely.geometry import shape
import shapefile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tanah.colab_models import haversine_km

OUT = ROOT / 'data/processed/akses_medan'
BOUNDS = (109.8, -8.8, 111.9, -6.7)
GROUPS = {'wisata': {'attraction', 'museum', 'theme_park'}, 'kampus': {'university', 'college'}}


def write_csv(name, rows):
    with (OUT / name).open('w', newline='') as stream:
        w = csv.DictWriter(stream, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def read_pois(folder):
    records = []
    for layer in ['gis_osm_pois_free_1', 'gis_osm_pois_a_free_1']:
        with shapefile.Reader(str(folder / (layer + '.shp')), encodingErrors='replace') as reader:
            for item in reader.iterShapeRecords(bbox=BOUNDS):
                attrs = item.record.as_dict()
                for group, classes in GROUPS.items():
                    if attrs['fclass'] not in classes:
                        continue
                    geom = shape(item.shape.__geo_interface__)
                    point = geom.representative_point()
                    if BOUNDS[0] <= point.x <= BOUNDS[2] and BOUNDS[1] <= point.y <= BOUNDS[3]:
                        records.append(dict(kelompok=group, kelas=attrs['fclass'], layer=layer,
                                            osm_id=attrs['osm_id'], lon=point.x, lat=point.y))
    if not all(any(r['kelompok'] == g for r in records) for g in GROUPS):
        raise ValueError('Kelompok POI kosong.')
    return records


def terrain(src, geom):
    win = geometry_window(src, [geom], pad_x=2, pad_y=2)
    data = src.read(1, window=win, masked=True).astype(float).filled(np.nan)
    tr = src.window_transform(win)
    mask = geometry_mask([geom], data.shape, tr, invert=True)
    # Central differences on the full tile window before restricting to the polygon.
    lat = tr.f + (np.arange(data.shape[0]) + .5)*tr.e
    dy, dx = np.gradient(data)
    dy /= abs(tr.e) * 111195
    dx /= (tr.a * 111195 * np.cos(np.radians(lat)))[:, None]
    slope = np.degrees(np.arctan(np.hypot(dx, dy)))
    valid = mask & np.isfinite(data) & np.isfinite(slope)
    coverage = valid.sum()/mask.sum()
    if coverage < .95:
        raise ValueError(f'Cakupan DEM terlalu rendah: {coverage:.3f}')
    return dict(elevasi_median_m=float(np.median(data[valid])), lereng_median_derajat=float(np.median(slope[valid])),
                n_sel_valid=int(valid.sum()), fraksi_valid=float(coverage))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    folder = ROOT / 'data/raw/osm_210101'
    dem = ROOT / 'data/raw/srtm/srtm_59_14.zip'
    geometry = ROOT / 'hasil/audit_spasial/solo_raya.geojson'
    with (ROOT / 'data/koordinat.csv').open() as stream:
        points = {(r['kab_kota'], r['kecamatan']): (float(r['lat']), float(r['lon'])) for r in csv.DictReader(stream)}
    pois = read_pois(folder)
    rows = []
    with rasterio.open(f'zip://{dem}!srtm_59_14.tif') as src:
        for f in json.loads(geometry.read_text())['features']:
            p = f['properties']
            row = {k: p[k] for k in ('kab_kota', 'kecamatan')}
            lat, lon = points[tuple(row.values())]
            row.update(terrain(src, f['geometry']))
            for group in GROUPS:
                subset = [r for r in pois if r['kelompok'] == group]
                distances = haversine_km([lat], [lon], [r['lat'] for r in subset], [r['lon'] for r in subset])[0]
                row['jarak_' + group + '_km'] = float(distances.min())
                margin = min(lon-BOUNDS[0], BOUNDS[2]-lon, lat-BOUNDS[1], BOUNDS[3]-lat)*108
                if distances.min() >= margin:
                    raise ValueError('Perluas cakupan ekstraksi POI.')
            rows.append(row)
    if len(rows) != 127 or {(r['kab_kota'], r['kecamatan']) for r in rows} != set(points):
        raise ValueError('Kunci spasial tidak lengkap.')
    write_csv('fitur.csv', rows)
    write_csv('poi_osm.csv', pois)
    paths = [dem, geometry, ROOT/'data/koordinat.csv', *sorted(folder.glob('gis_osm_*')), OUT/'fitur.csv', OUT/'poi_osm.csv']
    manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (OUT/'sha256.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print('127 kecamatan;', {g: sum(r['kelompok']==g for r in pois) for g in GROUPS})


if __name__ == '__main__':
    main()
