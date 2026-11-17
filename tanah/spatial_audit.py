"""Audit titik, padanan dan poligon; buat peta statis yang dapat diperiksa."""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pyproj import Transformer
from shapely.geometry import Point, shape, mapping
from shapely.ops import transform, unary_union
from shapely.validation import explain_validity

from .coordinates import norm, region
from .config import ROOT, KEY


def audit(geojson, coordinates, aliases, output):
    output.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ROOT / "data/harga_tanah_2020.csv")
    coords = pd.read_csv(coordinates)
    assert len(coords) == 127 and not coords.duplicated(KEY).any()
    joined = df.merge(coords, on=KEY, validate="one_to_one")
    assert len(joined) == 127
    alias = {(region(r.kab_kota), norm(r.kecamatan)): (region(r.kab_sumber), norm(r.kec_sumber))
             for r in pd.read_csv(aliases).itertuples()}
    source = json.loads(geojson.read_text())
    features = source["features"]
    assert len(features) == 576, "Ekspor BIG Jawa Tengah harus lengkap: 576 kecamatan"
    assert len({f['properties']['objectid'] for f in features}) == 576
    lookup = {}
    for f in features:
        p = f["properties"]
        lookup.setdefault((region(p["wadmkk"]), norm(p["wadmkc"])), []).append(f)
    project = Transformer.from_crs(4326, 32749, always_xy=True).transform
    records, polygons, selected = [], {}, []
    for i, row in enumerate(joined.itertuples(), 1):
        key = (region(row.kab_kota), norm(row.kecamatan))
        matches = lookup[alias.get(key, key)]
        codes = {f['properties']['kdcpum'] for f in matches}
        assert len(codes) == 1, f"Padanan kode ambigu: {key}"
        for f in matches:
            g = shape(f['geometry'])
            assert g.is_valid, (key, explain_validity(g))
        geometry = unary_union([shape(f["geometry"]) for f in matches])
        pt = Point(row.lon, row.lat)
        inside = geometry.contains(pt)
        projected = transform(project, geometry)
        point_projected = transform(project, pt)
        assert inside and projected.contains(point_projected), f"Titik di luar {key}"
        expected = projected.representative_point()
        # GDAL/GEOS union ordering can select an alternative valid surface point.
        polygons[(row.kab_kota, row.kecamatan)] = geometry
        props = matches[0]['properties']
        records.append({"nomor_peta": i, "kab_kota": row.kab_kota, "kecamatan": row.kecamatan,
            "kab_sumber": props['wadmkk'], "kec_sumber": props['wadmkc'], "kode_sumber": next(iter(codes)),
            "objectid": ';'.join(str(f['properties']['objectid']) for f in matches),
            "metadata": props['metadata'], "padanan": "eksplisit" if key in alias else "normalisasi",
            "lat": row.lat, "lon": row.lon, "di_dalam_poligon": inside,
            "jarak_ke_batas_m": point_projected.distance(projected.boundary),
            "luas_km2": projected.area / 1e6,
            "selisih_point_on_surface_m": point_projected.distance(expected)})
        selected.append({"type": "Feature", "properties": {"kab_kota": row.kab_kota,
            "kecamatan": row.kecamatan, "kode_sumber": next(iter(codes))}, "geometry": mapping(geometry)})
    audit_df = pd.DataFrame(records)
    audit_df.to_csv(output / 'padanan_dan_titik.csv', index=False)
    (output / 'solo_raya.geojson').write_text(json.dumps({"type": "FeatureCollection", "features": selected}))
    regions = sorted(df.kab_kota.unique())
    def draw(ax, rows, title):
        for row in rows.itertuples():
            geom = transform(project, polygons[(row.kab_kota, row.kecamatan)])
            color = plt.get_cmap('tab10')(regions.index(row.kab_kota))
            parts = [geom] if geom.geom_type == 'Polygon' else geom.geoms
            for part in parts:
                x, y = part.exterior.xy
                ax.fill([v/1000 for v in x], [v/1000 for v in y], color=color, alpha=.18)
                ax.plot([v/1000 for v in x], [v/1000 for v in y], color=color, linewidth=.5)
                for hole in part.interiors:
                    x, y = hole.xy
                    ax.fill([v/1000 for v in x], [v/1000 for v in y], color='white')
            x, y = project(row.lon, row.lat)
            ax.plot(x/1000, y/1000, 'ko', ms=2)
            ax.annotate(str(row.nomor_peta), (x/1000, y/1000), xytext=(2,2),
                        textcoords='offset points', fontsize=6)
        ax.set_aspect('equal')
        ax.set_title(title, fontsize=10)
        ax.set_xlabel('UTM 49S easting (km)')
        ax.set_ylabel('Northing (km)')
        ax.tick_params(labelsize=7)
    fig, axes = plt.subplots(2, 4, figsize=(22, 13))
    draw(axes.flat[0], audit_df, 'Solo Raya — 127 titik')
    for ax, reg in zip(axes.flat[1:], regions):
        rows = audit_df[audit_df.kab_kota == reg]
        draw(ax, rows, f'{reg} ({len(rows)})')
    fig.suptitle('Audit titik representatif: BIG metadata 2023-09-28; observasi harga 2020\nNomor merujuk padanan_dan_titik.csv; batas historis 2020 belum dipastikan', fontsize=14)
    fig.tight_layout(rect=(0,0,1,.94))
    fig.savefig(output / 'peta_audit.png', dpi=160)
    fig.savefig(output / 'peta_audit.pdf')
    plt.close(fig)
    for reg in regions:
        rows = audit_df[audit_df.kab_kota == reg]
        fig, ax = plt.subplots(figsize=(9,9))
        draw(ax, rows, reg)
        fig.tight_layout()
        fig.savefig(output / (region(reg).replace(' ', '_') + '.png'), dpi=130)
        plt.close(fig)
    print(f"127/127 titik di dalam poligon; 127 padanan unik. Jarak minimum ke batas: {audit_df.jarak_ke_batas_m.min():.2f} m")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--geojson', type=Path, default=ROOT/'data/jawa_tengah_big.geojson')
    p.add_argument('--koordinat', type=Path, default=ROOT/'data/koordinat.csv')
    p.add_argument('--padanan', type=Path, default=ROOT/'data/padanan_nama.csv')
    p.add_argument('--output', type=Path, default=ROOT/'hasil/audit_spasial')
    a=p.parse_args()
    audit(a.geojson,a.koordinat,a.padanan,a.output)
