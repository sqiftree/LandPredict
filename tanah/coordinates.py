"""Bangun titik representatif kecamatan dari GeoJSON WGS84 dengan GDAL."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import pandas as pd

from .config import ROOT, KEY


def norm(name):
    return " ".join(str(name).strip().casefold().split())


def region(name):
    return norm(name).removeprefix("kabupaten ").removeprefix("kota ")


def prepare(geojson, kab_field, kec_field, output, aliases=None):
    if not shutil.which("ogr2ogr"):
        raise ValueError("Pasang GDAL atau gunakan OSGeo4W Shell dari QGIS.")
    df = pd.read_csv(ROOT / "data/harga_tanah_2020.csv")[KEY]
    names = {(region(k), norm(c)): (k, c) for k, c in df.itertuples(index=False)}
    if len(names) != 127 or df.duplicated(KEY).any():
        raise ValueError("Data harus memuat 127 kunci unik.")
    replacements = {}
    if aliases:
        for row in pd.read_csv(aliases).itertuples(index=False):
            source_key = (region(row.kab_sumber), norm(row.kec_sumber))
            target_key = (region(row.kab_kota), norm(row.kecamatan))
            if target_key not in names or source_key in replacements:
                raise ValueError(f"Padanan tidak valid atau duplikat: {source_key}")
            replacements[source_key] = target_key
    source = json.loads(geojson.read_text(encoding="utf-8-sig"))
    if source.get("type") != "FeatureCollection":
        raise ValueError("Input harus GeoJSON FeatureCollection.")
    if source.get("crs") and not any(s in str(source["crs"]).upper() for s in ("4326", "CRS84")):
        raise ValueError("Ekspor ulang batas sebagai GeoJSON WGS84.")
    parts = []
    found = set()
    for feature in source["features"]:
        fields = feature["properties"]
        key = (region(fields[kab_field]), norm(fields[kec_field]))
        key = replacements.get(key, key)
        if key not in names:
            continue
        geometry = feature.get("geometry")
        if not geometry or geometry["type"] not in ("Polygon", "MultiPolygon"):
            raise ValueError(f"Geometri wilayah harus berupa poligon: {key}")
        found.add(key)
        parts.append({"type":"Feature", "properties":dict(zip(KEY,names[key])), "geometry":geometry})
    missing = names.keys() - found
    if missing:
        raise ValueError("Periksa padanan wilayah: " + ", ".join("/".join(k) for k in sorted(missing)))
    with tempfile.TemporaryDirectory() as tmp:
        work = Path(tmp)
        raw = work / "wilayah.geojson"
        raw.write_text(json.dumps({"type":"FeatureCollection","features":parts}),encoding="utf-8")
        subprocess.run(["ogr2ogr","-f","GPKG","-s_srs","EPSG:4326","-t_srs","EPSG:32749",
                        str(work/"utm.gpkg"),str(raw),"-nln","batas"],check=True)
        sql = ("SELECT kab_kota, kecamatan, ST_PointOnSurface(ST_Union(geom)) AS geom "
               "FROM batas GROUP BY kab_kota, kecamatan")
        subprocess.run(["ogr2ogr","-f","GeoJSON","-dialect","SQLite","-sql",sql,
                        "-t_srs","EPSG:4326",str(work/"titik.json"),str(work/"utm.gpkg")],check=True)
        points = json.loads((work/"titik.json").read_text(encoding="utf-8"))
    records = []
    for f in points["features"]:
        lon, lat = f["geometry"]["coordinates"][:2]
        props = f["properties"]
        records.append([props["kab_kota"], props["kecamatan"], lat, lon])
    coordinates = pd.DataFrame(records,columns=KEY+["lat","lon"])
    merged = df.merge(coordinates,on=KEY,how="left",validate="one_to_one")
    if merged.isna().any().any():
        raise ValueError("Ada kecamatan tanpa titik.")
    output.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output,index=False)
    print(f"{len(merged)} titik tersimpan di {output}. Periksa peta dan tahun batas sebelum pemodelan.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("geojson",type=Path)
    parser.add_argument("--kab",required=True,help="Nama atribut kabupaten/kota pada sumber")
    parser.add_argument("--kec",required=True,help="Nama atribut kecamatan pada sumber")
    parser.add_argument("--output",type=Path,default=ROOT/"data/koordinat.csv")
    parser.add_argument("--padanan", type=Path, help="CSV padanan eksplisit, tanpa fuzzy matching")
    args = parser.parse_args()
    prepare(args.geojson,args.kab,args.kec,args.output,args.padanan)
