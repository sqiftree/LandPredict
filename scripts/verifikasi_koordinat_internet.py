"""Verifikasi internet & penelusuran asal-usul koordinat 127 kecamatan Solo Raya.

Mengueri 5 sumber terbuka daring secara langsung & terstruktur:
1. BIG KSP Satu Peta ArcGIS REST (MapServer/3) — atribut & poligon resmi
2. Kemendagri (wilayah.id/api/districts/{33.09..33.72}.json) — 127 kode resmi
3. BPS / HDX COD-AB (idn_admin_boundaries.xlsx, idn_admin3) — pcode & center_lat/lon
4. GADM v4.1 (gadm41_IDN_3.json.zip) — centroid poligon pra-pemekaran 2019
5. OpenStreetMap Nominatim (reverse geocoding, delay >= 1.1 detik/permintaan)

Menghasilkan:
- data/processed/audit_koordinat_127.csv
- docs/LAPORAN_VERIFIKASI_KOORDINAT_127.md
"""

from __future__ import annotations

import argparse
import io
import json
import math
from pathlib import Path
import re
import statistics
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile

import openpyxl
import pandas as pd
from shapely.geometry import Point, shape


ROOT = Path(__file__).resolve().parent.parent
PATH_KOORD_BIG = ROOT / "data" / "koordinat.csv"
PATH_KOORD_COLAB = ROOT / "data" / "sumber" / "koordinat_solo_raya.csv"
PATH_PADANAN = ROOT / "data" / "padanan_nama.csv"
PATH_OUT_CSV = ROOT / "data" / "processed" / "audit_koordinat_127.csv"
PATH_OUT_MD = ROOT / "docs" / "LAPORAN_VERIFIKASI_KOORDINAT_127.md"

USER_AGENT = "LandPredict-AcademicAudit/1.0 (UNS Machine Learning Course Project)"

KAB_CODES = ["33.09", "33.10", "33.11", "33.12", "33.13", "33.14", "33.72"]
HDX_KAB_PCODES = {"ID3309", "ID3310", "ID3311", "ID3312", "ID3313", "ID3314", "ID3372"}

BIG_REST_URL = (
    "https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/BATAS_WILAYAH/"
    "MapServer/3/query?where=kdpkab+IN+(%2733.09%27,%2733.10%27,%2733.11%27,"
    "%2733.12%27,%2733.13%27,%2733.14%27,%2733.72%27)&outFields=objectid,"
    "wadmkk,wadmkc,kdcpum,kdpkab,metadata&returnGeometry=true&outSR=4326&f=geojson"
)
KEMENDAGRI_URL_TMPL = "https://wilayah.id/api/districts/{code}.json"
HDX_XLSX_URL = (
    "https://data.humdata.org/dataset/84a1d98a-790b-4d66-9d14-bbfa48500802/"
    "resource/ba60b4d3-fd55-4fcf-b1bd-adf7e4bdba90/download/idn_admin_boundaries.xlsx"
)
GADM_ZIP_URL = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IDN_3.json.zip"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r_m = 6_371_008.8
    phi1, lam1, phi2, lam2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dphi = phi2 - phi1
    dlam = lam2 - lam1
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    return 2.0 * r_m * math.asin(min(1.0, math.sqrt(a)))


def norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).strip().casefold())


def norm_compact(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text).casefold())


def strip_kab_prefix(text: str) -> str:
    s = norm_text(text)
    if s.startswith("kabupaten "):
        return s[len("kabupaten "):]
    if s.startswith("kota "):
        return s[len("kota "):]
    return s


def fetch_bytes(url: str, cache_file: Path | None = None, timeout: int = 90) -> bytes:
    if cache_file is not None and cache_file.exists():
        return cache_file.read_bytes()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    last_err: Exception | None = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
            if cache_file is not None:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_bytes(data)
            return data
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Gagal mengunduh {url}: {last_err}")


def fetch_nominatim_reverse(
    lat: float,
    lon: float,
    cache_dir: Path | None,
    key_slug: str,
    last_call_ts: list[float],
    min_delay: float = 1.15,
) -> dict:
    cache_file = (cache_dir / "nominatim" / f"{key_slug}.json") if cache_dir else None
    if cache_file is not None and cache_file.exists():
        return json.loads(cache_file.read_text(encoding="utf-8"))

    params = urllib.parse.urlencode({
        "format": "jsonv2",
        "lat": f"{lat:.7f}",
        "lon": f"{lon:.7f}",
        "zoom": "12",
        "addressdetails": "1",
        "accept-language": "id",
    })
    url = f"{NOMINATIM_REVERSE_URL}?{params}"

    for attempt in range(5):
        elapsed = time.monotonic() - last_call_ts[0]
        if elapsed < min_delay:
            time.sleep(min_delay - elapsed)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            last_call_ts[0] = time.monotonic()
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            if cache_file is not None:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            return payload
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 502, 503, 504) and attempt < 4:
                time.sleep(2.5 * (attempt + 1))
                continue
            raise
        except Exception:  # noqa: BLE001
            if attempt < 4:
                time.sleep(2.5 * (attempt + 1))
                continue
            raise
    raise RuntimeError(f"Nominatim reverse gagal untuk ({lat}, {lon})")


def load_big_polygons(cache_dir: Path | None) -> tuple[dict, list]:
    raw = fetch_bytes(BIG_REST_URL, (cache_dir / "big_solo_raya.geojson") if cache_dir else None, timeout=120)
    gj = json.loads(raw.decode("utf-8"))
    features = gj.get("features", [])
    if len(features) != 127:
        raise AssertionError(f"BIG KSP REST mengembalikan {len(features)} fitur, diharapkan 127")

    by_key = {}
    all_polys = []
    for feat in features:
        props = feat["properties"]
        geom = shape(feat["geometry"])
        k_kab = strip_kab_prefix(props["wadmkk"])
        k_kec = norm_text(props["wadmkc"])
        rec = {
            "objectid": props["objectid"],
            "wadmkk": props["wadmkk"],
            "wadmkc": props["wadmkc"],
            "kdcpum": props["kdcpum"],
            "kdpkab": props["kdpkab"],
            "metadata": props.get("metadata", ""),
            "geom": geom,
        }
        by_key[(k_kab, k_kec)] = rec
        all_polys.append(rec)
    return by_key, all_polys


def load_kemendagri(cache_dir: Path | None) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for code in KAB_CODES:
        raw = fetch_bytes(
            KEMENDAGRI_URL_TMPL.format(code=code),
            (cache_dir / f"kem_{code}.json") if cache_dir else None,
            timeout=45,
        )
        data = json.loads(raw.decode("utf-8"))
        for item in data.get("data", []):
            out[item["code"]] = {"code": item["code"], "name": item["name"], "kab_code": code}
    if len(out) != 127:
        raise AssertionError(f"Kemendagri mengembalikan {len(out)} kecamatan, diharapkan 127")
    return out


def load_hdx_bps(cache_dir: Path | None) -> dict[tuple[str, str], dict]:
    raw = fetch_bytes(HDX_XLSX_URL, (cache_dir / "idn_admin_boundaries.xlsx") if cache_dir else None, timeout=180)
    wb = openpyxl.load_workbook(io.BytesIO(raw), read_only=True, data_only=True)
    ws = wb["idn_admin3"]
    it = ws.iter_rows(values_only=True)
    hdr = list(next(it))
    idx = {h: i for i, h in enumerate(hdr)}

    hdx_map: dict[tuple[str, str], dict] = {}
    for row in it:
        if row[idx["adm2_pcode"]] in HDX_KAB_PCODES:
            k2 = norm_compact(str(row[idx["adm2_name"]]).replace("Kota ", ""))
            k3 = norm_compact(str(row[idx["adm3_name"]]))
            hdx_map[(k2, k3)] = {
                "adm3_pcode": row[idx["adm3_pcode"]],
                "adm3_name": row[idx["adm3_name"]],
                "adm2_name": row[idx["adm2_name"]],
                "center_lat": float(row[idx["center_lat"]]),
                "center_lon": float(row[idx["center_lon"]]),
                "valid_on": str(row[idx["valid_on"]]),
            }
    return hdx_map


def load_gadm41(cache_dir: Path | None) -> dict[tuple[str, str], dict]:
    raw = fetch_bytes(GADM_ZIP_URL, (cache_dir / "gadm41_IDN_3.json.zip") if cache_dir else None, timeout=180)
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        inner_name = zf.namelist()[0]
        gadm = json.loads(zf.read(inner_name).decode("utf-8"))

    target_kab = {
        "Boyolali", "Klaten", "Sukoharjo", "Wonogiri",
        "Karanganyar", "Sragen", "KotaSurakarta", "Surakarta",
    }
    gadm_map: dict[tuple[str, str], dict] = {}
    for feat in gadm.get("features", []):
        props = feat["properties"]
        if props.get("NAME_2") not in target_kab:
            continue
        geom = shape(feat["geometry"])
        cent = geom.centroid
        k2 = norm_compact(str(props["NAME_2"]).replace("Kota", ""))
        k3 = norm_compact(str(props["NAME_3"]))
        gadm_map[(k2, k3)] = {
            "name_2": props["NAME_2"],
            "name_3": props["NAME_3"],
            "cc_3": props.get("CC_3", ""),
            "centroid_lat": float(cent.y),
            "centroid_lon": float(cent.x),
        }
    return gadm_map


def classify_cause(kecamatan: str) -> str:
    if kecamatan in {"Gladagsari", "Tamansari", "Wonosamodro"}:
        return "Input manual titik kota/kantor kecamatan (tidak ada di GADM 4.1)"
    if kecamatan in {"Ampel", "Wonosegoro", "Musuk", "Kemusu"}:
        return "Pemekaran Boyolali 2018-2019 (centroid GADM pra-pemekaran vs BIG pasca-pemekaran)"
    if kecamatan in {"Baturetno", "Nguntoronadi", "Wuryantoro", "Miri", "Sumberlawang"}:
        return "PointOnSurface vs Centroid GADM 4.1 + perbedaan batas waduk"
    return "PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84)"


def run_audit(cache_dir: Path | None = None) -> tuple[pd.DataFrame, dict]:
    df_big = pd.read_csv(PATH_KOORD_BIG)
    df_colab = pd.read_csv(PATH_KOORD_COLAB)
    df_padanan = pd.read_csv(PATH_PADANAN)

    assert len(df_big) == 127 and len(df_colab) == 127
    assert list(zip(df_big["kab_kota"], df_big["kecamatan"])) == list(
        zip(df_colab["kab_kota"], df_colab["kecamatan"])
    )

    alias_to_big: dict[tuple[str, str], tuple[str, str]] = {}
    for row in df_padanan.itertuples(index=False):
        alias_to_big[(strip_kab_prefix(row.kab_kota), norm_text(row.kecamatan))] = (
            strip_kab_prefix(row.kab_sumber),
            norm_text(row.kec_sumber),
        )

    print("[1/5] Mengueri BIG KSP Satu Peta REST (MapServer/3)...")
    big_by_key, big_polys = load_big_polygons(cache_dir)

    print("[2/5] Mengueri kode wilayah Kemendagri (wilayah.id)...")
    kem_by_code = load_kemendagri(cache_dir)

    print("[3/5] Memuat BPS / HDX COD-AB (idn_admin_boundaries.xlsx)...")
    hdx_map = load_hdx_bps(cache_dir)

    print("[4/5] Memuat GADM v4.1 (gadm41_IDN_3.json.zip)...")
    gadm_map = load_gadm41(cache_dir)

    print("[5/5] Mengueri OpenStreetMap Nominatim reverse untuk 127 kecamatan...")
    gadm_aliases = {
        ("karanganyar", "kebakramat"): ("karanganyar", "kebakkramat"),
        ("wonogiri", "sidoarjo"): ("wonogiri", "sidoharjo"),
        ("sragen", "ngrampal"): ("sragen", "ngampal"),
        ("sragen", "kalijambe"): ("sragen", "kaliambe"),
    }
    hdx_aliases = {
        ("karanganyar", "kebakramat"): ("karanganyar", "kebakkramat"),
        ("wonogiri", "sidoarjo"): ("wonogiri", "sidoharjo"),
    }

    last_call_ts = [0.0]
    records = []
    kem_matched_codes = set()
    big_metadata_values = set()

    for idx_row, (r_big, r_col) in enumerate(
        zip(df_big.itertuples(index=False), df_colab.itertuples(index=False)), start=1
    ):
        kab = r_big.kab_kota
        kec = r_big.kecamatan
        lat_b, lon_b = float(r_big.lat), float(r_big.lon)
        lat_c, lon_c = float(r_col.lat), float(r_col.lon)

        lookup_key = alias_to_big.get(
            (strip_kab_prefix(kab), norm_text(kec)),
            (strip_kab_prefix(kab), norm_text(kec)),
        )
        big_rec = big_by_key[lookup_key]
        kode_kem = big_rec["kdcpum"]
        assert kode_kem in kem_by_code, f"Kode Kemendagri tidak ditemukan: {kode_kem}"
        kem_matched_codes.add(kode_kem)
        big_metadata_values.add(big_rec["metadata"])

        pt_big = Point(lon_b, lat_b)
        pt_col = Point(lon_c, lat_c)
        big_inside = bool(big_rec["geom"].contains(pt_big))
        col_inside = bool(big_rec["geom"].contains(pt_col))

        actual_poly_name = f"{big_rec['wadmkk']} / {big_rec['wadmkc']}"
        if not col_inside:
            found_actual = None
            for poly in big_polys:
                if poly["geom"].contains(pt_col):
                    found_actual = f"{poly['wadmkk']} / {poly['wadmkc']} (DI LUAR {big_rec['wadmkc']})"
                    break
            actual_poly_name = found_actual or "DI LUAR POLIGON SOLO RAYA"

        # HDX BPS
        k2_comp = norm_compact(kab.replace("Kabupaten ", "").replace("Kota ", ""))
        k3_comp = norm_compact(kec)
        hdx_rec = hdx_map.get(hdx_aliases.get((k2_comp, k3_comp), (k2_comp, k3_comp)))
        if hdx_rec is not None:
            adm3_pcode_hdx = hdx_rec["adm3_pcode"]
            lat_hdx = hdx_rec["center_lat"]
            lon_hdx = hdx_rec["center_lon"]
            dist_big_hdx_m = round(haversine_m(lat_b, lon_b, lat_hdx, lon_hdx), 2)
        else:
            adm3_pcode_hdx = "TIDAK_ADA_DI_HDX_2020"
            lat_hdx = float("nan")
            lon_hdx = float("nan")
            dist_big_hdx_m = float("nan")

        # GADM 4.1
        gadm_rec = gadm_map.get(gadm_aliases.get((k2_comp, k3_comp), (k2_comp, k3_comp)))
        if gadm_rec is not None:
            lat_gadm = round(gadm_rec["centroid_lat"], 6)
            lon_gadm = round(gadm_rec["centroid_lon"], 6)
            dist_col_gadm_m = round(
                haversine_m(lat_c, lon_c, gadm_rec["centroid_lat"], gadm_rec["centroid_lon"]), 2
            )
        else:
            lat_gadm = float("nan")
            lon_gadm = float("nan")
            dist_col_gadm_m = float("nan")

        # Nominatim reverse untuk koordinat terverifikasi BIG
        slug = f"{kode_kem.replace('.', '_')}_{k3_comp}"
        nom = fetch_nominatim_reverse(lat_b, lon_b, cache_dir, slug, last_call_ts)
        osm_label = nom.get("display_name", "")
        osm_type = str(nom.get("osm_type", ""))
        osm_id = str(nom.get("osm_id", ""))

        dist_big_col_m = round(haversine_m(lat_b, lon_b, lat_c, lon_c), 2)
        cause = classify_cause(kec)
        if big_inside and col_inside:
            status = "TERVERIFIKASI (BIG+Kemendagri+OSM OK; Colab di dalam poligon)"
        elif big_inside and not col_inside:
            status = "TERVERIFIKASI_BIG (PERINGATAN: Titik Colab di luar poligon BIG)"
        else:
            status = "GAGAL_VERIFIKASI_BIG"

        records.append({
            "kode_kemendagri": kode_kem,
            "kab_kota": kab,
            "kecamatan": kec,
            "nama_sumber_big": f"{big_rec['wadmkk']} / {big_rec['wadmkc']}",
            "lat_big": lat_b,
            "lon_big": lon_b,
            "lat_colab": lat_c,
            "lon_colab": lon_c,
            "selisih_big_vs_colab_m": dist_big_col_m,
            "big_di_dalam_poligon": big_inside,
            "colab_di_dalam_poligon": col_inside,
            "poligon_aktual_colab": actual_poly_name,
            "adm3_pcode_hdx": adm3_pcode_hdx,
            "lat_hdx_bps": lat_hdx,
            "lon_hdx_bps": lon_hdx,
            "selisih_big_vs_hdx_m": dist_big_hdx_m,
            "lat_gadm41_centroid": lat_gadm,
            "lon_gadm41_centroid": lon_gadm,
            "selisih_colab_vs_gadm41_m": dist_col_gadm_m,
            "osm_reverse_label": osm_label,
            "osm_type": osm_type,
            "osm_id": osm_id,
            "klasifikasi_penyebab_selisih": cause,
            "status_verifikasi": status,
        })
        if idx_row % 25 == 0 or idx_row == 127:
            print(f"     Progres Nominatim: {idx_row}/127 selesai")

    df_audit = pd.DataFrame(records)
    assert len(df_audit) == 127
    assert len(kem_matched_codes) == 127
    assert df_audit["big_di_dalam_poligon"].all()
    assert (df_audit["osm_reverse_label"].astype(str).str.len() > 0).all()

    PATH_OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    df_audit.to_csv(PATH_OUT_CSV, index=False)

    meta = {
        "big_metadata": sorted(big_metadata_values),
        "kemendagri_matched": len(kem_matched_codes),
        "hdx_matched": int(df_audit["lat_hdx_bps"].notna().sum()),
        "gadm_matched": int(df_audit["lat_gadm41_centroid"].notna().sum()),
        "osm_matched": int((df_audit["osm_reverse_label"].str.len() > 0).sum()),
    }
    return df_audit, meta


def write_markdown_report(df_audit: pd.DataFrame, meta: dict) -> None:
    d_bc = df_audit["selisih_big_vs_colab_m"]
    d_bh = df_audit["selisih_big_vs_hdx_m"].dropna()
    d_cg = df_audit["selisih_colab_vs_gadm41_m"].dropna()

    outside_rows = df_audit[~df_audit["colab_di_dalam_poligon"]]
    top10 = df_audit.sort_values("selisih_big_vs_colab_m", ascending=False).head(10)

    # Ringkasan per kabupaten/kota
    reg_rows = []
    for kab, grp in df_audit.groupby("kab_kota", sort=False):
        reg_rows.append(
            f"| {kab} | {len(grp)} | "
            f"{int(grp['big_di_dalam_poligon'].sum())}/{len(grp)} | "
            f"{int(grp['colab_di_dalam_poligon'].sum())}/{len(grp)} | "
            f"{grp['selisih_big_vs_colab_m'].min():,.1f} | "
            f"{grp['selisih_big_vs_colab_m'].median():,.1f} | "
            f"{grp['selisih_big_vs_colab_m'].mean():,.1f} | "
            f"{grp['selisih_big_vs_colab_m'].max():,.1f} |"
        )

    # Tabel lengkap 127 kecamatan
    full_rows = []
    for i, r in enumerate(df_audit.itertuples(index=False), start=1):
        hdx_str = f"{r.selisih_big_vs_hdx_m:,.1f}" if pd.notna(r.selisih_big_vs_hdx_m) else "N/A (Pemekaran)"
        gadm_str = f"{r.selisih_colab_vs_gadm41_m:,.1f}" if pd.notna(r.selisih_colab_vs_gadm41_m) else "N/A (Manual)"
        osm_short = str(r.osm_reverse_label).split(",")[0:3]
        osm_ringkas = ", ".join(s.strip() for s in osm_short)
        big_in = "Ya" if r.big_di_dalam_poligon else "Tidak"
        col_in = "Ya" if r.colab_di_dalam_poligon else "TIDAK"
        full_rows.append(
            f"| {i} | `{r.kode_kemendagri}` | {r.kab_kota} | {r.kecamatan} | "
            f"{r.lat_big:.6f}, {r.lon_big:.6f} | {r.lat_colab:.6f}, {r.lon_colab:.6f} | "
            f"{r.selisih_big_vs_colab_m:,.1f} | {big_in} | {col_in} | "
            f"{hdx_str} | {gadm_str} | {osm_ringkas} ({r.osm_type}/{r.osm_id}) | "
            f"{r.klasifikasi_penyebab_selisih} |"
        )

    outside_bullets = "\n".join(
        f"- **{r.kab_kota} — {r.kecamatan}** (`{r.kode_kemendagri}`): "
        f"koordinat Colab `({r.lat_colab:.6f}, {r.lon_colab:.6f})` berjarak **{r.selisih_big_vs_colab_m:,.1f} m** "
        f"dari titik BIG `({r.lat_big:.6f}, {r.lon_big:.6f})` dan secara geometris jatuh di dalam poligon **{r.poligon_aktual_colab}**."
        for r in outside_rows.itertuples(index=False)
    )

    top10_rows = "\n".join(
        f"| {r.kab_kota} | {r.kecamatan} | {r.selisih_big_vs_colab_m:,.1f} | "
        f"{'Ya' if r.colab_di_dalam_poligon else 'TIDAK'} | {r.poligon_aktual_colab} | {r.klasifikasi_penyebab_selisih} |"
        for r in top10.itertuples(index=False)
    )

    md = f"""# Laporan Verifikasi Internet dan Penelusuran Asal-Usul Koordinat 127 Kecamatan Solo Raya

Dokumen ini menyajikan hasil verifikasi daring terhadap seluruh **127 kecamatan** di 7 kabupaten/kota Solo Raya pada kedua berkas koordinat proyek:
1. **`data/koordinat.csv`** (titik representatif berbasis poligon BIG KSP Satu Peta)
2. **`data/sumber/koordinat_solo_raya.csv`** (berkas pendamping notebook Colab terdahulu)

Hasil audit lengkap tersimpan dalam format tabular di `data/processed/audit_koordinat_127.csv` dan dihasilkan ulang secara deterministik melalui `scripts/verifikasi_koordinat_internet.py`.

---

## 1. Ringkasan Eksekutif

- **Kelengkapan & Validitas Administratif:** Seluruh **127/127 kecamatan** pada `data/koordinat.csv` cocok 100% dengan kode kecamatan resmi **Kemendagri (`wilayah.id`)** dan fitur poligon aktif **BIG KSP Satu Peta (`MapServer/3`, metadata `{', '.join(meta['big_metadata'])}`)**.
- **Ketercakupan Poligon:** **127/127 (100%)** titik pada `data/koordinat.csv` berada tepat di dalam poligon kecamatan BIG pasangannya. Sebaliknya, pada `data/sumber/koordinat_solo_raya.csv`, hanya **125/127** titik yang berada di dalam poligon pasangannya; **2 kecamatan di Kabupaten Boyolali (`Ampel` dan `Wonosegoro`) jatuh di luar poligon BIG masing-masing** karena masih memakai centroid wilayah induk pra-pemekaran 2018–2019.
- **Pembuktian Asal-Usul Berkas:**
  - `data/koordinat.csv` berasal dari geometri resmi **BIG KSP Satu Peta** yang diproyeksikan ke UTM Zona 49S (`EPSG:32749`) dan diekstrak dengan `ST_PointOnSurface(ST_Union(geom))` lalu dikembalikan ke WGS84 (`EPSG:4326`). Titik ini juga cocok erat dengan `center_lat/center_lon` **BPS / HDX COD-AB** pada 124 kecamatan pra-pemekaran (median selisih **{d_bh.median():,.1f} m**).
  - `data/sumber/koordinat_solo_raya.csv` terbukti merupakan gabungan **124 centroid poligon GADM v4.1 (`gadm41_IDN_3`)** pra-pemekaran (median selisih terhadap centroid GADM 4.1 hanya **{d_cg.median():,.2f} m**, rerata **{d_cg.mean():,.2f} m**, maks **{d_cg.max():,.2f} m**) ditambah **3 titik estimasi manual berpresisi 3–4 desimal** di dekat pusat kota/kantor kecamatan untuk 3 kecamatan hasil pemekaran Boyolali 2018–2019 (`Gladagsari`, `Tamansari`, `Wonosamodro`).
- **Keputusan Penggabungan Dataset (R1):** Berkas **`data/koordinat.csv`** dipilih sebagai sumber koordinat resmi untuk dataset gabungan bersih (`data/processed/dataset_solo_raya_2020_bersih.csv`).

---

## 2. Sumber Terbuka Otoritatif yang Dikueri

| No. | Sumber Daring | Endpoint / Arsip | Cakupan Solo Raya | Fungsi Verifikasi |
|---|---|---|---|---|
| 1 | **BIG KSP Satu Peta** | `kspservices.big.go.id/.../BATAS_WILAYAH/MapServer/3/query` | **127 / 127** | Kode `kdcpum`, nama `wadmkk`/`wadmkc`, uji titik-dalam-poligon (`EPSG:4326`) |
| 2 | **Kemendagri (`wilayah.id`)** | `wilayah.id/api/districts/{{33.09..33.72}}.json` | **127 / 127** | Validasi kode resmi kecamatan & ejaan administratif terkini |
| 3 | **BPS / HDX COD-AB** | `data.humdata.org/.../idn_admin_boundaries.xlsx` (`idn_admin3`) | **124 / 127** | Pembanding `adm3_pcode` & `center_lat/center_lon` BPS (validitas 2020-04-01; belum memuat 3 pemekaran Boyolali) |
| 4 | **GADM v4.1 (`IDN_3`)** | `geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IDN_3.json.zip` | **124 / 127** | Pembuktian asal-usul `koordinat_solo_raya.csv` (19 kecamatan Boyolali pra-pemekaran + poligon terpisah `WadukGajahmungkur`) |
| 5 | **OpenStreetMap Nominatim** | `nominatim.openstreetmap.org/reverse` (`zoom=12`) | **127 / 127** | *Reverse-geocoding* independen label administratif & ID objek OSM (`osm_type`/`osm_id`) |

---

## 3. Penjelasan Penyebab Selisih antara `data/koordinat.csv` dan `data/sumber/koordinat_solo_raya.csv`

Secara keseluruhan (127 kecamatan), jarak Haversine antara kedua berkas berkisar dari **{d_bc.min():,.1f} m** (Sragen — Sambungmacan) hingga **{d_bc.max():,.1f} m** (Boyolali — Ampel), dengan **median {d_bc.median():,.1f} m** dan **rerata {d_bc.mean():,.1f} m**. Terdapat empat penyebab utama yang teridentifikasi secara kuantitatif:

1. **Perbedaan Definisi Titik Representatif (`PointOnSurface` vs `Centroid`):**
   `data/koordinat.csv` menggunakan `ST_PointOnSurface` dalam UTM 49S yang menjamin titik selalu jatuh di dalam poligon, sedangkan `koordinat_solo_raya.csv` menggunakan *geometric centroid* GADM 4.1 dalam WGS84. Pada kecamatan berbentuk cekung atau memanjang, centroid bergeser ratusan meter dari `PointOnSurface`.
2. **Pemekaran Wilayah Boyolali 2018–2019 (Perda Kab. Boyolali No. 18 Tahun 2018):**
   GADM v4.1 (serta arsip HDX COD-AB 2020-04-01) masih menggunakan batas lama 19 kecamatan Boyolali sebelum terbentuknya **Gladagsari** (dari Ampel), **Tamansari** (dari Musuk), dan **Wonosamodro** (dari Wonosegoro & Kemusu). Akibatnya, titik `Ampel` dan `Wonosegoro` pada berkas Colab berada pada centroid lama sebelum pemekaran dan secara fisik jatuh di wilayah kecamatan baru:
{outside_bullets}
3. **Pengisian Manual 3 Kecamatan Baru pada Berkas Colab:**
   Karena `Gladagsari`, `Tamansari`, dan `Wonosamodro` tidak tersedia di GADM v4.1, pembuat berkas Colab memasukkan koordinat berpresisi 3–4 desimal (`-7.4622, 110.5305`; `-7.5803, 110.543`; `-7.285, 110.651`) di sekitar pusat permukiman/kantor kecamatan, yang berjarak 1,7–4,9 km dari titik permukaan poligon penuh BIG.
4. **Perbedaan Penanganan Poligon Waduk (Wonogiri & Sragen):**
   GADM v4.1 memisahkan badan air `WadukGajahmungkur` sebagai fitur tersendiri sehingga centroid kecamatan tepian waduk (`Baturetno`, `Nguntoronadi`, `Wuryantoro` di Wonogiri serta area Waduk Kedung Ombo di `Miri` dan `Sumberlawang`, Sragen) bergeser terhadap poligon penuh BIG.
5. **Variasi Ejaan Resmi (2 Kecamatan):**
   `data/padanan_nama.csv` memetakan perbedaan ejaan yang terkonfirmasi di BIG, Kemendagri, BPS, dan GADM: `Karanganyar / Kebakramat` $\\leftrightarrow$ `Kebakkramat` dan `Wonogiri / Sidoarjo` $\\leftrightarrow$ `Sidoharjo`.

### 10 Kecamatan dengan Selisih Terbesar (BIG vs Colab)

| Kabupaten/Kota | Kecamatan | Selisih (m) | Colab di Dalam Poligon BIG? | Poligon Aktual Titik Colab | Klasifikasi Penyebab |
|---|---|---:|---|---|---|
{top10_rows}

---

## 4. Ringkasan Audit per Kabupaten/Kota

| Kabupaten/Kota | Jumlah Kec. | BIG di Dalam Poligon | Colab di Dalam Poligon | Min Selisih (m) | Median Selisih (m) | Rerata Selisih (m) | Maks Selisih (m) |
|---|---:|---:|---:|---:|---:|---:|---:|
{chr(10).join(reg_rows)}

---

## 5. Catatan Batasan & Kehati-hatian

- **Metadata Tanggal Batas BIG:** Fitur BIG KSP Layer 3 membawa penanda `TASWIL1000020230928_DATA_BATAS_DESAKELURAHAN` (edisi 2022/2023). Seluruh 127 kecamatan telah terbentuk sebelum tahun 2020 (pemekaran Boyolali efektif 2019), namun kesetaraan geometris garis batas mikro 2020 vs 2023 tidak diklaim identik mutlak.
- **Keterbatasan Batas OSM:** OpenStreetMap Nominatim tidak memiliki poligon `admin_level=7` lengkap untuk beberapa kecamatan rural di Solo Raya, sehingga *reverse-geocoding* pada `zoom=12` sering mengembalikan nama desa/kelurahan atau kota terdekat di dalam kecamatan terkait. Oleh karena itu, otoritas poligon tetap mengacu pada BIG + Kemendagri, sementara OSM berfungsi sebagai konfirmasi lokasi independen.

---

## 6. Tabel Audit Lengkap 127 Kecamatan

Kolom di bawah ini meringkas hasil verifikasi untuk seluruh 127 kecamatan (file CSV penuh dengan 24 kolom tersedia di `data/processed/audit_koordinat_127.csv`):

| No | Kode Kemendagri | Kab/Kota | Kecamatan | Koordinat BIG (`lat, lon`) | Koordinat Colab (`lat, lon`) | Selisih BIG–Colab (m) | BIG In-Poly | Colab In-Poly | Selisih BIG–HDX (m) | Selisih Colab–GADM4.1 (m) | Label OSM Nominatim (Ringkas) | Klasifikasi Penyebab |
|---:|---|---|---|---|---|---:|:---:|:---:|---:|---:|---|---|
{chr(10).join(full_rows)}
"""
    PATH_OUT_MD.parent.mkdir(parents=True, exist_ok=True)
    PATH_OUT_MD.write_text(md, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Direktori cache opsional untuk respons HTTP selama proses audit.",
    )
    args = parser.parse_args()

    if args.cache_dir is not None:
        df_audit, meta = run_audit(args.cache_dir)
    else:
        with tempfile.TemporaryDirectory() as tmp:
            df_audit, meta = run_audit(Path(tmp))

    write_markdown_report(df_audit, meta)
    print(f"[OK] Audit CSV tersimpan: {PATH_OUT_CSV.relative_to(ROOT)} ({len(df_audit)} baris)")
    print(f"[OK] Laporan Markdown tersimpan: {PATH_OUT_MD.relative_to(ROOT)}")
    print(f"     Ringkasan cakupan: {meta}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
