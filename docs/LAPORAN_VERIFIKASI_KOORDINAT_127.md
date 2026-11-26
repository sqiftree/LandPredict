# Laporan Verifikasi Internet dan Penelusuran Asal-Usul Koordinat 127 Kecamatan Solo Raya

Dokumen ini menyajikan hasil verifikasi daring terhadap seluruh **127 kecamatan** di 7 kabupaten/kota Solo Raya pada kedua berkas koordinat proyek:
1. **`data/koordinat.csv`** (titik representatif berbasis poligon BIG KSP Satu Peta)
2. **`data/sumber/koordinat_solo_raya.csv`** (berkas pendamping notebook Colab terdahulu)

Hasil audit lengkap tersimpan dalam format tabular di `data/processed/audit_koordinat_127.csv` dan dihasilkan ulang secara deterministik melalui `scripts/verifikasi_koordinat_internet.py`.

---

## 1. Ringkasan Eksekutif

- **Kelengkapan & Validitas Administratif:** Seluruh **127/127 kecamatan** pada `data/koordinat.csv` cocok 100% dengan kode kecamatan resmi **Kemendagri (`wilayah.id`)** dan fitur poligon aktif **BIG KSP Satu Peta (`MapServer/3`, metadata `TASWIL1000020230928_DATA_BATAS_DESAKELURAHAN`)**.
- **Ketercakupan Poligon:** **127/127 (100%)** titik pada `data/koordinat.csv` berada tepat di dalam poligon kecamatan BIG pasangannya. Sebaliknya, pada `data/sumber/koordinat_solo_raya.csv`, hanya **125/127** titik yang berada di dalam poligon pasangannya; **2 kecamatan di Kabupaten Boyolali (`Ampel` dan `Wonosegoro`) jatuh di luar poligon BIG masing-masing** karena masih memakai centroid wilayah induk pra-pemekaran 2018–2019.
- **Pembuktian Asal-Usul Berkas:**
  - `data/koordinat.csv` berasal dari geometri resmi **BIG KSP Satu Peta** yang diproyeksikan ke UTM Zona 49S (`EPSG:32749`) dan diekstrak dengan `ST_PointOnSurface(ST_Union(geom))` lalu dikembalikan ke WGS84 (`EPSG:4326`). Titik ini juga cocok erat dengan `center_lat/center_lon` **BPS / HDX COD-AB** pada 124 kecamatan pra-pemekaran (median selisih **96.1 m**).
  - `data/sumber/koordinat_solo_raya.csv` terbukti merupakan gabungan **124 centroid poligon GADM v4.1 (`gadm41_IDN_3`)** pra-pemekaran (median selisih terhadap centroid GADM 4.1 hanya **11.50 m**, rerata **13.17 m**, maks **48.50 m**) ditambah **3 titik estimasi manual berpresisi 3–4 desimal** di dekat pusat kota/kantor kecamatan untuk 3 kecamatan hasil pemekaran Boyolali 2018–2019 (`Gladagsari`, `Tamansari`, `Wonosamodro`).
- **Keputusan Penggabungan Dataset (R1):** Berkas **`data/koordinat.csv`** dipilih sebagai sumber koordinat resmi untuk dataset gabungan bersih (`data/processed/dataset_solo_raya_2020_bersih.csv`).

---

## 2. Sumber Terbuka Otoritatif yang Dikueri

| No. | Sumber Daring | Endpoint / Arsip | Cakupan Solo Raya | Fungsi Verifikasi |
|---|---|---|---|---|
| 1 | **BIG KSP Satu Peta** | `kspservices.big.go.id/.../BATAS_WILAYAH/MapServer/3/query` | **127 / 127** | Kode `kdcpum`, nama `wadmkk`/`wadmkc`, uji titik-dalam-poligon (`EPSG:4326`) |
| 2 | **Kemendagri (`wilayah.id`)** | `wilayah.id/api/districts/{33.09..33.72}.json` | **127 / 127** | Validasi kode resmi kecamatan & ejaan administratif terkini |
| 3 | **BPS / HDX COD-AB** | `data.humdata.org/.../idn_admin_boundaries.xlsx` (`idn_admin3`) | **124 / 127** | Pembanding `adm3_pcode` & `center_lat/center_lon` BPS (validitas 2020-04-01; belum memuat 3 pemekaran Boyolali) |
| 4 | **GADM v4.1 (`IDN_3`)** | `geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IDN_3.json.zip` | **124 / 127** | Pembuktian asal-usul `koordinat_solo_raya.csv` (19 kecamatan Boyolali pra-pemekaran + poligon terpisah `WadukGajahmungkur`) |
| 5 | **OpenStreetMap Nominatim** | `nominatim.openstreetmap.org/reverse` (`zoom=12`) | **127 / 127** | *Reverse-geocoding* independen label administratif & ID objek OSM (`osm_type`/`osm_id`) |

---

## 3. Penjelasan Penyebab Selisih antara `data/koordinat.csv` dan `data/sumber/koordinat_solo_raya.csv`

Secara keseluruhan (127 kecamatan), jarak Haversine antara kedua berkas berkisar dari **37.0 m** (Sragen — Sambungmacan) hingga **5,667.2 m** (Boyolali — Ampel), dengan **median 597.2 m** dan **rerata 759.5 m**. Terdapat empat penyebab utama yang teridentifikasi secara kuantitatif:

1. **Perbedaan Definisi Titik Representatif (`PointOnSurface` vs `Centroid`):**
   `data/koordinat.csv` menggunakan `ST_PointOnSurface` dalam UTM 49S yang menjamin titik selalu jatuh di dalam poligon, sedangkan `koordinat_solo_raya.csv` menggunakan *geometric centroid* GADM 4.1 dalam WGS84. Pada kecamatan berbentuk cekung atau memanjang, centroid bergeser ratusan meter dari `PointOnSurface`.
2. **Pemekaran Wilayah Boyolali 2018–2019 (Perda Kab. Boyolali No. 18 Tahun 2018):**
   GADM v4.1 (serta arsip HDX COD-AB 2020-04-01) masih menggunakan batas lama 19 kecamatan Boyolali sebelum terbentuknya **Gladagsari** (dari Ampel), **Tamansari** (dari Musuk), dan **Wonosamodro** (dari Wonosegoro & Kemusu). Akibatnya, titik `Ampel` dan `Wonosegoro` pada berkas Colab berada pada centroid lama sebelum pemekaran dan secara fisik jatuh di wilayah kecamatan baru:
- **Kabupaten Boyolali — Ampel** (`33.09.02`): koordinat Colab `(-7.451395, 110.517850)` berjarak **5,667.2 m** dari titik BIG `(-7.461912, 110.568145)` dan secara geometris jatuh di dalam poligon **Boyolali / Gladagsari (DI LUAR Ampel)**.
- **Kabupaten Boyolali — Wonosegoro** (`33.09.18`): koordinat Colab `(-7.282192, 110.655003)` berjarak **4,229.3 m** dari titik BIG `(-7.292808, 110.691824)` dan secara geometris jatuh di dalam poligon **Boyolali / Wonosamodro (DI LUAR Wonosegoro)**.
3. **Pengisian Manual 3 Kecamatan Baru pada Berkas Colab:**
   Karena `Gladagsari`, `Tamansari`, dan `Wonosamodro` tidak tersedia di GADM v4.1, pembuat berkas Colab memasukkan koordinat berpresisi 3–4 desimal (`-7.4622, 110.5305`; `-7.5803, 110.543`; `-7.285, 110.651`) di sekitar pusat permukiman/kantor kecamatan, yang berjarak 1,7–4,9 km dari titik permukaan poligon penuh BIG.
4. **Perbedaan Penanganan Poligon Waduk (Wonogiri & Sragen):**
   GADM v4.1 memisahkan badan air `WadukGajahmungkur` sebagai fitur tersendiri sehingga centroid kecamatan tepian waduk (`Baturetno`, `Nguntoronadi`, `Wuryantoro` di Wonogiri serta area Waduk Kedung Ombo di `Miri` dan `Sumberlawang`, Sragen) bergeser terhadap poligon penuh BIG.
5. **Variasi Ejaan Resmi (2 Kecamatan):**
   `data/padanan_nama.csv` memetakan perbedaan ejaan yang terkonfirmasi di BIG, Kemendagri, BPS, dan GADM: `Karanganyar / Kebakramat` $\leftrightarrow$ `Kebakkramat` dan `Wonogiri / Sidoarjo` $\leftrightarrow$ `Sidoharjo`.

### 10 Kecamatan dengan Selisih Terbesar (BIG vs Colab)

| Kabupaten/Kota | Kecamatan | Selisih (m) | Colab di Dalam Poligon BIG? | Poligon Aktual Titik Colab | Klasifikasi Penyebab |
|---|---|---:|---|---|---|
| Kabupaten Boyolali | Ampel | 5,667.2 | TIDAK | Boyolali / Gladagsari (DI LUAR Ampel) | Pemekaran Boyolali 2018-2019 (centroid GADM pra-pemekaran vs BIG pasca-pemekaran) |
| Kabupaten Boyolali | Gladagsari | 4,949.2 | Ya | Boyolali / Gladagsari | Input manual titik kota/kantor kecamatan (tidak ada di GADM 4.1) |
| Kabupaten Boyolali | Wonosegoro | 4,229.3 | TIDAK | Boyolali / Wonosamodro (DI LUAR Wonosegoro) | Pemekaran Boyolali 2018-2019 (centroid GADM pra-pemekaran vs BIG pasca-pemekaran) |
| Kabupaten Wonogiri | Nguntoronadi | 1,758.3 | Ya | Wonogiri / Nguntoronadi | PointOnSurface vs Centroid GADM 4.1 + perbedaan batas waduk |
| Kabupaten Boyolali | Musuk | 1,690.3 | Ya | Boyolali / Musuk | Pemekaran Boyolali 2018-2019 (centroid GADM pra-pemekaran vs BIG pasca-pemekaran) |
| Kabupaten Wonogiri | Jatipurno | 1,606.3 | Ya | Wonogiri / Jatipurno | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| Kabupaten Wonogiri | Karangtengah | 1,494.8 | Ya | Wonogiri / Karangtengah | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| Kabupaten Sragen | Miri | 1,467.7 | Ya | Sragen / Miri | PointOnSurface vs Centroid GADM 4.1 + perbedaan batas waduk |
| Kabupaten Karanganyar | Matesih | 1,461.1 | Ya | Karanganyar / Matesih | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| Kabupaten Sragen | Jenar | 1,435.0 | Ya | Sragen / Jenar | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |

---

## 4. Ringkasan Audit per Kabupaten/Kota

| Kabupaten/Kota | Jumlah Kec. | BIG di Dalam Poligon | Colab di Dalam Poligon | Min Selisih (m) | Median Selisih (m) | Rerata Selisih (m) | Maks Selisih (m) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Kota Surakarta | 5 | 5/5 | 5/5 | 71.6 | 134.1 | 246.1 | 610.5 |
| Kabupaten Boyolali | 22 | 22/22 | 20/22 | 365.3 | 819.8 | 1,361.4 | 5,667.2 |
| Kabupaten Sukoharjo | 12 | 12/12 | 12/12 | 64.3 | 513.5 | 583.8 | 1,262.3 |
| Kabupaten Karanganyar | 17 | 17/17 | 17/17 | 238.0 | 647.9 | 765.0 | 1,461.1 |
| Kabupaten Wonogiri | 25 | 25/25 | 25/25 | 60.8 | 863.1 | 755.2 | 1,758.3 |
| Kabupaten Sragen | 20 | 20/20 | 20/20 | 37.0 | 610.6 | 704.7 | 1,467.7 |
| Kabupaten Klaten | 26 | 26/26 | 26/26 | 55.4 | 386.8 | 472.6 | 1,412.5 |

---

## 5. Catatan Batasan & Kehati-hatian

- **Metadata Tanggal Batas BIG:** Fitur BIG KSP Layer 3 membawa penanda `TASWIL1000020230928_DATA_BATAS_DESAKELURAHAN` (edisi 2022/2023). Seluruh 127 kecamatan telah terbentuk sebelum tahun 2020 (pemekaran Boyolali efektif 2019), namun kesetaraan geometris garis batas mikro 2020 vs 2023 tidak diklaim identik mutlak.
- **Keterbatasan Batas OSM:** OpenStreetMap Nominatim tidak memiliki poligon `admin_level=7` lengkap untuk beberapa kecamatan rural di Solo Raya, sehingga *reverse-geocoding* pada `zoom=12` sering mengembalikan nama desa/kelurahan atau kota terdekat di dalam kecamatan terkait. Oleh karena itu, otoritas poligon tetap mengacu pada BIG + Kemendagri, sementara OSM berfungsi sebagai konfirmasi lokasi independen.

---

## 6. Tabel Audit Lengkap 127 Kecamatan

Kolom di bawah ini meringkas hasil verifikasi untuk seluruh 127 kecamatan (file CSV penuh dengan 24 kolom tersedia di `data/processed/audit_koordinat_127.csv`):

| No | Kode Kemendagri | Kab/Kota | Kecamatan | Koordinat BIG (`lat, lon`) | Koordinat Colab (`lat, lon`) | Selisih BIG–Colab (m) | BIG In-Poly | Colab In-Poly | Selisih BIG–HDX (m) | Selisih Colab–GADM4.1 (m) | Label OSM Nominatim (Ringkas) | Klasifikasi Penyebab |
|---:|---|---|---|---|---|---:|:---:|:---:|---:|---:|---|---|
| 1 | `33.72.05` | Kota Surakarta | Banjarsari | -7.546681, 110.816211 | -7.547348, 110.817175 | 129.5 | Ya | Ya | 59.4 | 12.4 | Banjarsari, Surakarta, Jawa Tengah (node/10951565578) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 2 | `33.72.04` | Kota Surakarta | Jebres | -7.554141, 110.853051 | -7.554370, 110.847517 | 610.5 | Ya | Ya | 9.1 | 10.3 | Jebres, Surakarta, Jawa Tengah (node/10951565577) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 3 | `33.72.01` | Kota Surakarta | Laweyan | -7.561702, 110.793771 | -7.561327, 110.793243 | 71.6 | Ya | Ya | 606.0 | 11.3 | Banjarsari, Surakarta, Jawa Tengah (node/10951565578) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 4 | `33.72.03` | Kota Surakarta | Pasar Kliwon | -7.579991, 110.832201 | -7.581052, 110.831623 | 134.1 | Ya | Ya | 21.3 | 9.6 | Kecamatan Pasar Kliwon, Jawa Tengah, Indonesia (way/331519449) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 5 | `33.72.02` | Kota Surakarta | Serengan | -7.581984, 110.815077 | -7.581855, 110.817657 | 284.8 | Ya | Ya | 29.7 | 9.0 | Kecamatan Serengan, Jawa Tengah, Indonesia (way/325339977) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 6 | `33.09.10` | Kabupaten Boyolali | Sambi | -7.479713, 110.692558 | -7.478725, 110.684923 | 848.8 | Ya | Ya | 87.6 | 14.2 | Sambi, Boyolali, Jawa Tengah (node/10951571609) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 7 | `33.09.12` | Kabupaten Boyolali | Nogosari | -7.460680, 110.751609 | -7.460425, 110.757094 | 605.4 | Ya | Ya | 240.8 | 19.8 | Nogosari, Boyolali, Jawa Tengah (node/10951571608) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 8 | `33.09.14` | Kabupaten Boyolali | Karanggede | -7.368829, 110.662354 | -7.370629, 110.657369 | 585.0 | Ya | Ya | 430.9 | 12.4 | Karanggede, Boyolali, Jawa Tengah (node/10951571635) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 9 | `33.09.06` | Kabupaten Boyolali | Mojosongo | -7.540198, 110.623477 | -7.545075, 110.614185 | 1,159.0 | Ya | Ya | 49.3 | 5.0 | Mojosongo, Boyolali, Jawa Tengah (node/10951565582) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 10 | `33.09.11` | Kabupaten Boyolali | Ngemplak | -7.507755, 110.778536 | -7.509133, 110.768360 | 1,132.3 | Ya | Ya | 1,454.9 | 16.2 | Kecamatan Ngemplak, Desa Dibal, Kecamatan Ngemplak (node/6539041518) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 11 | `33.09.02` | Kabupaten Boyolali | Ampel | -7.461912, 110.568145 | -7.451395, 110.517850 | 5,667.2 | Ya | TIDAK | 7,910.8 | 3.4 | Gladagsari, Boyolali, Jawa Tengah (node/11068103799) | Pemekaran Boyolali 2018-2019 (centroid GADM pra-pemekaran vs BIG pasca-pemekaran) |
| 12 | `33.09.18` | Kabupaten Boyolali | Wonosegoro | -7.292808, 110.691824 | -7.282192, 110.655003 | 4,229.3 | Ya | TIDAK | 3,396.6 | 3.3 | Wonosegoro, Boyolali, Jawa Tengah (node/10951571633) | Pemekaran Boyolali 2018-2019 (centroid GADM pra-pemekaran vs BIG pasca-pemekaran) |
| 13 | `33.09.13` | Kabupaten Boyolali | Simo | -7.431992, 110.673654 | -7.431018, 110.683740 | 1,117.3 | Ya | Ya | 329.0 | 14.2 | Simo, Boyolali, Jawa Tengah (node/1308681130) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 14 | `33.09.16` | Kabupaten Boyolali | Andong | -7.375661, 110.763716 | -7.367423, 110.763580 | 916.2 | Ya | Ya | 150.9 | 9.1 | Andong, Boyolali, Jawa Tengah (node/12394312782) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 15 | `33.09.05` | Kabupaten Boyolali | Boyolali | -7.516759, 110.590655 | -7.513388, 110.594144 | 537.1 | Ya | Ya | 204.4 | 10.6 | Boyolali, Jawa Tengah, 57313 (node/10957525358) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 16 | `33.09.04` | Kabupaten Boyolali | Musuk | -7.556373, 110.537696 | -7.568215, 110.528082 | 1,690.3 | Ya | Ya | 2,881.3 | 10.7 | Musuk, Boyolali, Jawa Tengah (node/10951571612) | Pemekaran Boyolali 2018-2019 (centroid GADM pra-pemekaran vs BIG pasca-pemekaran) |
| 17 | `33.09.07` | Kabupaten Boyolali | Teras | -7.540607, 110.653358 | -7.543851, 110.653877 | 365.3 | Ya | Ya | 139.2 | 23.2 | Teras, Boyolali, Jawa Tengah (node/10951565575) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 18 | `33.09.15` | Kabupaten Boyolali | Klego | -7.366944, 110.712418 | -7.369477, 110.709451 | 431.7 | Ya | Ya | 15.8 | 7.1 | Klego, Boyolali, Jawa Tengah (node/10951571634) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 19 | `33.09.03` | Kabupaten Boyolali | Cepogo | -7.505158, 110.522906 | -7.512267, 110.522705 | 790.8 | Ya | Ya | 1,116.4 | 17.0 | Cepogo, Boyolali, Jawa Tengah (node/10951571613) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 20 | `33.09.09` | Kabupaten Boyolali | Banyudono | -7.537021, 110.689919 | -7.537034, 110.694025 | 452.6 | Ya | Ya | 148.9 | 12.5 | Banyudono, Boyolali, Jawa Tengah (node/10951571611) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 21 | `33.09.17` | Kabupaten Boyolali | Kemusu | -7.281626, 110.756434 | -7.286780, 110.753448 | 661.0 | Ya | Ya | 2,281.4 | 19.0 | Kemusu, Boyolali, Jawa Tengah (node/12394312781) | Pemekaran Boyolali 2018-2019 (centroid GADM pra-pemekaran vs BIG pasca-pemekaran) |
| 22 | `33.09.19` | Kabupaten Boyolali | Juwangi | -7.207690, 110.740167 | -7.211405, 110.744968 | 671.7 | Ya | Ya | 29.1 | 6.5 | Juwangi, Boyolali, Jawa Tengah (node/10951571631) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 23 | `33.09.01` | Kabupaten Boyolali | Selo | -7.497401, 110.456669 | -7.499106, 110.450237 | 733.9 | Ya | Ya | 100.6 | 12.9 | Samiran, Selo, Boyolali (relation/3815014) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 24 | `33.09.08` | Kabupaten Boyolali | Sawit | -7.573351, 110.685837 | -7.573975, 110.689315 | 389.6 | Ya | Ya | 62.6 | 8.7 | Sawit, Boyolali, Jawa Tengah (node/10951571610) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 25 | `33.09.22` | Kabupaten Boyolali | Wonosamodro | -7.277037, 110.646514 | -7.285000, 110.651000 | 1,014.3 | Ya | Ya | N/A (Pemekaran) | N/A (Manual) | Wonosamodro, Boyolali, Jawa Tengah (node/12394312780) | Input manual titik kota/kantor kecamatan (tidak ada di GADM 4.1) |
| 26 | `33.09.21` | Kabupaten Boyolali | Tamansari | -7.584086, 110.534738 | -7.580300, 110.543000 | 1,003.2 | Ya | Ya | N/A (Pemekaran) | N/A (Manual) | Musuk, Boyolali, Jawa Tengah (node/10951571612) | Input manual titik kota/kantor kecamatan (tidak ada di GADM 4.1) |
| 27 | `33.09.20` | Kabupaten Boyolali | Gladagsari | -7.442530, 110.490233 | -7.462200, 110.530500 | 4,949.2 | Ya | Ya | N/A (Pemekaran) | N/A (Manual) | Ampel, Boyolali, Jawa Tengah (node/10951094624) | Input manual titik kota/kantor kecamatan (tidak ada di GADM 4.1) |
| 28 | `33.11.09` | Kabupaten Sukoharjo | Grogol | -7.611031, 110.816272 | -7.613193, 110.813555 | 384.0 | Ya | Ya | 1.6 | 3.2 | Grogol, Sukoharjo, Jawa Tengah (node/10951565601) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 29 | `33.11.04` | Kabupaten Sukoharjo | Sukoharjo | -7.674799, 110.808826 | -7.679778, 110.818748 | 1,225.5 | Ya | Ya | 14.3 | 22.7 | Sukoharjo, Jawa Tengah, 57511 (node/1204538477) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 30 | `33.11.01` | Kabupaten Sukoharjo | Weru | -7.784896, 110.756453 | -7.785245, 110.758379 | 215.7 | Ya | Ya | 163.7 | 10.9 | Weru, Sukoharjo, Jawa Tengah (node/12396104463) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 31 | `33.11.03` | Kabupaten Sukoharjo | Tawangsari | -7.726816, 110.792766 | -7.727933, 110.785340 | 827.6 | Ya | Ya | 35.8 | 19.8 | Tawangsari, Sukoharjo, Jawa Tengah (node/10951565573) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 32 | `33.11.07` | Kabupaten Sukoharjo | Polokarto | -7.647131, 110.903205 | -7.643998, 110.901412 | 400.6 | Ya | Ya | 110.2 | 4.4 | Polokarto, Sukoharjo, Jawa Tengah (node/10951565595) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 33 | `33.11.08` | Kabupaten Sukoharjo | Mojolaban | -7.596425, 110.871183 | -7.595849, 110.871237 | 64.3 | Ya | Ya | 18.2 | 18.3 | Bekonang, Sukoharjo, Jawa Tengah (node/10951565596) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 34 | `33.11.12` | Kabupaten Sukoharjo | Kartasura | -7.559566, 110.749099 | -7.557964, 110.747505 | 250.2 | Ya | Ya | 124.4 | 13.2 | Kartasura, Sukoharjo, Jawa Tengah (node/10951565602) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 35 | `33.11.02` | Kabupaten Sukoharjo | Bulu | -7.772032, 110.832968 | -7.767915, 110.829086 | 626.5 | Ya | Ya | 155.1 | 20.9 | Bulu, Sukoharjo, Jawa Tengah (relation/13024117) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 36 | `33.11.05` | Kabupaten Sukoharjo | Nguter | -7.742502, 110.895564 | -7.734178, 110.887774 | 1,262.3 | Ya | Ya | 24.6 | 14.7 | Nguter, Sukoharjo, Jawa Tengah (node/10951565574) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 37 | `33.11.06` | Kabupaten Sukoharjo | Bendosari | -7.682635, 110.897097 | -7.686837, 110.891762 | 751.0 | Ya | Ya | 126.8 | 7.2 | Bendosari, Sukoharjo, Jawa Tengah (node/10951565593) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 38 | `33.11.10` | Kabupaten Sukoharjo | Baki | -7.605875, 110.778997 | -7.607919, 110.778651 | 230.4 | Ya | Ya | 11.0 | 2.9 | Baki, Sukoharjo, Jawa Tengah (node/10951565600) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 39 | `33.11.11` | Kabupaten Sukoharjo | Gatak | -7.592910, 110.734797 | -7.590153, 110.741185 | 768.0 | Ya | Ya | 105.4 | 18.5 | Gatak, Sukoharjo, Jawa Tengah (node/10951565598) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 40 | `33.13.11` | Kabupaten Karanganyar | Jaten | -7.567353, 110.887136 | -7.564012, 110.894911 | 934.1 | Ya | Ya | 40.0 | 11.3 | Jaten, Karanganyar, Jawa Tengah (node/10951565592) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 41 | `33.13.14` | Kabupaten Karanganyar | Kebakramat | -7.521808, 110.919305 | -7.520291, 110.923662 | 509.0 | Ya | Ya | 74.2 | 4.5 | Kebakkramat, Karanganyar, Jawa Tengah (node/10951630649) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 42 | `33.13.09` | Kabupaten Karanganyar | Karanganyar | -7.600003, 110.978888 | -7.603282, 110.977769 | 384.9 | Ya | Ya | 97.5 | 30.5 | Karanganyar, Jawa Tengah, 57713 (node/3056671337) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 43 | `33.13.13` | Kabupaten Karanganyar | Gondangrejo | -7.503072, 110.853834 | -7.499476, 110.845393 | 1,012.8 | Ya | Ya | 117.7 | 5.1 | Jeruksawit, Karanganyar, Jawa Tengah (node/1308688164) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 44 | `33.13.12` | Kabupaten Karanganyar | Colomadu | -7.536546, 110.754430 | -7.535591, 110.760228 | 647.9 | Ya | Ya | 24.4 | 17.5 | Colomadu, Karanganyar, Jawa Tengah (node/10951565581) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 45 | `33.13.16` | Kabupaten Karanganyar | Kerjo | -7.541882, 111.056430 | -7.543320, 111.066626 | 1,135.2 | Ya | Ya | 64.0 | 7.0 | Kerjo, Karanganyar, Jawa Tengah (node/10951630653) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 46 | `33.13.10` | Kabupaten Karanganyar | Tasikmadu | -7.567305, 110.940920 | -7.569338, 110.938099 | 384.5 | Ya | Ya | 22.9 | 9.2 | Tasikmadu, Karanganyar, Jawa Tengah (node/10951565591) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 47 | `33.13.07` | Kabupaten Karanganyar | Ngargoyoso | -7.606191, 111.119445 | -7.609140, 111.123301 | 536.8 | Ya | Ya | 96.9 | 10.7 | Ngargoyoso, Karanganyar, Jawa Tengah (node/10951565585) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 48 | `33.13.06` | Kabupaten Karanganyar | Tawangmangu | -7.660827, 111.130358 | -7.663946, 111.138785 | 991.4 | Ya | Ya | 178.3 | 7.2 | Tawangmangu, Karanganyar, Jawa Tengah (node/10951565584) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 49 | `33.13.17` | Kabupaten Karanganyar | Jenawi | -7.565667, 111.132120 | -7.563135, 111.136777 | 585.5 | Ya | Ya | 39.4 | 9.3 | Jenawi, Karanganyar, Jawa Tengah (node/10951630654) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 50 | `33.13.15` | Kabupaten Karanganyar | Mojogedang | -7.552534, 110.992385 | -7.554200, 111.001956 | 1,071.1 | Ya | Ya | 15.9 | 21.2 | Mojogedang, Karanganyar, Jawa Tengah (node/10951565587) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 51 | `33.13.08` | Kabupaten Karanganyar | Karangpandan | -7.612190, 111.052539 | -7.616429, 111.062357 | 1,180.2 | Ya | Ya | 50.8 | 12.8 | Karangpandan, Karanganyar, Jawa Tengah (node/10951565588) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 52 | `33.13.01` | Kabupaten Karanganyar | Jatipuro | -7.749930, 111.009042 | -7.744948, 111.015061 | 864.1 | Ya | Ya | 72.0 | 11.5 | Jatipuro, Karanganyar, Jawa Tengah (node/10951630656) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 53 | `33.13.05` | Kabupaten Karanganyar | Matesih | -7.646171, 111.057185 | -7.643064, 111.044303 | 1,461.1 | Ya | Ya | 48.9 | 48.5 | Matesih, Karanganyar, Jawa Tengah (node/10951565589) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 54 | `33.13.02` | Kabupaten Karanganyar | Jatiyoso | -7.713782, 111.106918 | -7.712124, 111.105552 | 238.0 | Ya | Ya | 959.9 | 19.8 | Jatiyoso, Karanganyar, Jawa Tengah (node/10951630655) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 55 | `33.13.04` | Kabupaten Karanganyar | Jumantono | -7.654602, 110.993331 | -7.659725, 110.992573 | 575.8 | Ya | Ya | 8.6 | 17.4 | Jumantono, Karanganyar, Jawa Tengah (node/10951565590) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 56 | `33.13.03` | Kabupaten Karanganyar | Jumapolo | -7.709093, 111.006012 | -7.705841, 111.002968 | 493.3 | Ya | Ya | 131.8 | 5.0 | Jumapolo, Karanganyar, Jawa Tengah (node/10951565586) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 57 | `33.12.14` | Kabupaten Wonogiri | Sidoarjo | -7.863428, 111.055454 | -7.861350, 111.055735 | 233.2 | Ya | Ya | 276.2 | 8.7 | Sidorejo, Wonogiri, Jawa Tengah (node/10951630658) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 58 | `33.12.01` | Kabupaten Wonogiri | Pracimantoro | -8.078467, 110.820883 | -8.071704, 110.816091 | 918.7 | Ya | Ya | 122.5 | 10.3 | Pracimantoro, Wonogiri, Jawa Tengah (node/10951602031) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 59 | `33.12.12` | Kabupaten Wonogiri | Wonogiri | -7.803847, 110.937438 | -7.802210, 110.939589 | 298.8 | Ya | Ya | 463.6 | 10.7 | Selogiri, Wonogiri, Jawa Tengah (node/10951602035) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 60 | `33.12.22` | Kabupaten Wonogiri | Girimarto | -7.765627, 111.083660 | -7.775661, 111.085935 | 1,143.5 | Ya | Ya | 219.9 | 20.3 | Girimarto, Wonogiri, Jawa Tengah (node/10951630657) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 61 | `33.12.11` | Kabupaten Wonogiri | Selogiri | -7.791992, 110.884188 | -7.792709, 110.883309 | 125.4 | Ya | Ya | 7.5 | 26.6 | Selogiri, Wonogiri, Jawa Tengah (node/10951602035) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 62 | `33.12.08` | Kabupaten Wonogiri | Eromoko | -7.961524, 110.830563 | -7.967247, 110.821350 | 1,197.6 | Ya | Ya | 742.4 | 16.9 | Eromoko, Wonogiri, Jawa Tengah (node/10951602029) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 63 | `33.12.19` | Kabupaten Wonogiri | Slogohimo | -7.809725, 111.188067 | -7.818300, 111.190357 | 986.3 | Ya | Ya | 140.2 | 8.9 | Slogohimo, Wonogiri, Jawa Tengah (node/14003807423) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 64 | `33.12.09` | Kabupaten Wonogiri | Wuryantoro | -7.898977, 110.860451 | -7.897836, 110.855085 | 604.4 | Ya | Ya | 1,045.0 | 29.3 | Wuryantoro, Wonogiri, Jawa Tengah (node/10951602025) | PointOnSurface vs Centroid GADM 4.1 + perbedaan batas waduk |
| 65 | `33.12.13` | Kabupaten Wonogiri | Ngadirojo | -7.835128, 111.001221 | -7.827043, 111.005387 | 1,009.3 | Ya | Ya | 44.5 | 16.0 | Ngadirojo, Wonogiri, Jawa Tengah (node/14003807420) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 66 | `33.12.20` | Kabupaten Wonogiri | Jatisrono | -7.847631, 111.132074 | -7.844745, 111.132968 | 335.7 | Ya | Ya | 23.4 | 8.9 | Jatisrono, Wonogiri, Jawa Tengah (node/10951602011) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 67 | `33.12.17` | Kabupaten Wonogiri | Purwantoro | -7.834725, 111.263401 | -7.835128, 111.261836 | 178.1 | Ya | Ya | 155.7 | 15.0 | Purwantoro, Wonogiri, Jawa Tengah (node/10951602013) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 68 | `33.12.21` | Kabupaten Wonogiri | Jatipurno | -7.768830, 111.152906 | -7.778186, 111.141798 | 1,606.3 | Ya | Ya | 637.4 | 10.6 | Jatipurno, Wonogiri, Jawa Tengah (node/10951602010) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 69 | `33.12.10` | Kabupaten Wonogiri | Manyaran | -7.850638, 110.822579 | -7.845546, 110.815457 | 967.5 | Ya | Ya | 64.7 | 9.6 | Manyaran, Wonogiri, Jawa Tengah (node/10951565571) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 70 | `33.12.07` | Kabupaten Wonogiri | Baturetno | -7.956720, 110.936321 | -7.964330, 110.937862 | 863.1 | Ya | Ya | 1,088.3 | 20.1 | Baturetno, Wonogiri, Jawa Tengah (node/10951602028) | PointOnSurface vs Centroid GADM 4.1 + perbedaan batas waduk |
| 71 | `33.12.06` | Kabupaten Wonogiri | Nguntoronadi | -7.892583, 110.952079 | -7.897660, 110.967198 | 1,758.3 | Ya | Ya | 2,234.9 | 12.9 | Nguntoronadi, Wonogiri, Jawa Tengah (node/10951602026) | PointOnSurface vs Centroid GADM 4.1 + perbedaan batas waduk |
| 72 | `33.12.03` | Kabupaten Wonogiri | Giriwoyo | -8.034601, 110.951086 | -8.038518, 110.946648 | 654.6 | Ya | Ya | 856.5 | 8.8 | Giriwoyo, Wonogiri, Jawa Tengah (node/10951602030) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 73 | `33.12.05` | Kabupaten Wonogiri | Tirtomoyo | -7.962485, 111.084827 | -7.953874, 111.084272 | 959.4 | Ya | Ya | 908.3 | 3.9 | Tirtomoyo, Wonogiri, Jawa Tengah (node/10959875456) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 74 | `33.12.02` | Kabupaten Wonogiri | Giritontro | -8.089824, 110.901569 | -8.093928, 110.892521 | 1,095.7 | Ya | Ya | 408.1 | 6.9 | Giritontro, Wonogiri, Jawa Tengah (node/10951602032) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 75 | `33.12.25` | Kabupaten Wonogiri | Puhpelem | -7.772999, 111.268095 | -7.768419, 111.265671 | 575.0 | Ya | Ya | 259.3 | 3.9 | Puhpelem, Wonogiri, Jawa Tengah (node/1308658035) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 76 | `33.12.04` | Kabupaten Wonogiri | Batuwarno | -7.984485, 111.008163 | -7.983945, 111.008074 | 60.8 | Ya | Ya | 297.5 | 13.6 | Batuwarno, Wonogiri, Jawa Tengah (node/10951602027) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 77 | `33.12.16` | Kabupaten Wonogiri | Kismantoro | -7.903804, 111.241066 | -7.903507, 111.243683 | 290.1 | Ya | Ya | 87.6 | 15.1 | Kismantoro, Wonogiri, Jawa Tengah (node/10951602015) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 78 | `33.12.24` | Kabupaten Wonogiri | Paranggupito | -8.168707, 110.864590 | -8.170056, 110.864246 | 154.7 | Ya | Ya | 128.4 | 9.4 | Paranggupito, Wonogiri, Jawa Tengah (node/10951602034) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 79 | `33.12.15` | Kabupaten Wonogiri | Jatiroto | -7.895825, 111.130978 | -7.895544, 111.122849 | 895.9 | Ya | Ya | 318.1 | 2.9 | Jatiroto, Wonogiri, Jawa Tengah (node/10951602022) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 80 | `33.12.23` | Kabupaten Wonogiri | Karangtengah | -8.021903, 111.080984 | -8.029706, 111.069929 | 1,494.8 | Ya | Ya | 2,874.2 | 20.0 | Karangtengah, Wonogiri, Jawa Tengah (node/10951602018) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 81 | `33.12.18` | Kabupaten Wonogiri | Bulukerto | -7.761896, 111.213626 | -7.765107, 111.216451 | 473.7 | Ya | Ya | 68.9 | 8.2 | Bulukerto, Wonogiri, Jawa Tengah (node/10951630659) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 82 | `33.14.07` | Kabupaten Sragen | Sambungmacan | -7.369954, 111.101242 | -7.370265, 111.101360 | 37.0 | Ya | Ya | 95.3 | 21.7 | Sambungmacan, Sragen, Jawa Tengah (node/12394512787) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 83 | `33.14.09` | Kabupaten Sragen | Karangmalang | -7.457659, 111.020585 | -7.455689, 111.020376 | 220.3 | Ya | Ya | 109.1 | 24.2 | Karangmalang, Sragen, Jawa Tengah (node/10951630650) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 84 | `33.14.03` | Kabupaten Sragen | Masaran | -7.482446, 110.932721 | -7.477887, 110.937222 | 709.4 | Ya | Ya | 12.9 | 6.1 | Masaran, Sragen, Jawa Tengah (node/10951630648) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 85 | `33.14.06` | Kabupaten Sragen | Gondang | -7.431034, 111.097795 | -7.432465, 111.099916 | 282.9 | Ya | Ya | 8.7 | 12.4 | Gondang, Sragen, Jawa Tengah (node/10951630641) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 86 | `33.14.10` | Kabupaten Sragen | Sragen | -7.399302, 111.013415 | -7.404680, 111.018669 | 832.6 | Ya | Ya | 50.4 | 11.5 | Sidoharjo, Sragen, Jawa Tengah (node/10959875449) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 87 | `33.14.04` | Kabupaten Sragen | Kedawung | -7.500582, 111.022640 | -7.497145, 111.026755 | 593.2 | Ya | Ya | 24.6 | 12.6 | Kedawung, Sragen, Jawa Tengah (node/10951630652) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 88 | `33.14.02` | Kabupaten Sragen | Plupuh | -7.446346, 110.878658 | -7.439565, 110.888688 | 1,338.5 | Ya | Ya | 3.8 | 5.8 | Plupuh, Sragen, Jawa Tengah (node/10951630646) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 89 | `33.14.08` | Kabupaten Sragen | Ngrampal | -7.392935, 111.048436 | -7.387359, 111.049785 | 637.6 | Ya | Ya | 93.5 | 13.0 | Ngrampal, Sragen, Jawa Tengah (node/10951630647) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 90 | `33.14.12` | Kabupaten Sragen | Tanon | -7.382586, 110.923327 | -7.382617, 110.917669 | 624.0 | Ya | Ya | 1.3 | 10.2 | Tanon, Sragen, Jawa Tengah (node/10951630645) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 91 | `33.14.20` | Kabupaten Sragen | Jenar | -7.302934, 111.098581 | -7.308639, 111.110251 | 1,435.0 | Ya | Ya | 98.9 | 15.6 | Jenar, Sragen, Jawa Tengah (node/10951630638) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 92 | `33.14.01` | Kabupaten Sragen | Kalijambe | -7.433691, 110.821821 | -7.435971, 110.813577 | 943.7 | Ya | Ya | 125.7 | 1.3 | Kalijambe, Sragen, Jawa Tengah (node/10951571605) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 93 | `33.14.13` | Kabupaten Sragen | Gemolong | -7.395393, 110.836064 | -7.395804, 110.841019 | 548.2 | Ya | Ya | 92.8 | 25.7 | Gemolong, Sragen, Jawa Tengah (node/10951571606) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 94 | `33.14.05` | Kabupaten Sragen | Sambirejo | -7.495417, 111.113489 | -7.497316, 111.108422 | 597.2 | Ya | Ya | 32.5 | 17.6 | Sambirejo, Sragen, Jawa Tengah (node/10951630651) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 95 | `33.14.14` | Kabupaten Sragen | Miri | -7.332328, 110.813128 | -7.345459, 110.811768 | 1,467.7 | Ya | Ya | 2,455.6 | 41.2 | Miri, Sragen, Jawa Tengah (node/10951630644) | PointOnSurface vs Centroid GADM 4.1 + perbedaan batas waduk |
| 96 | `33.14.19` | Kabupaten Sragen | Tangen | -7.299833, 111.047484 | -7.291027, 111.056934 | 1,430.1 | Ya | Ya | 80.7 | 0.6 | Tangen, Sragen, Jawa Tengah (node/10951630637) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 97 | `33.14.17` | Kabupaten Sragen | Sukodono | -7.327845, 110.966661 | -7.325117, 110.975284 | 998.2 | Ya | Ya | 35.5 | 13.5 | Sukodono, Sragen, Jawa Tengah (node/10951630636) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 98 | `33.14.15` | Kabupaten Sragen | Sumberlawang | -7.315250, 110.872421 | -7.314049, 110.867843 | 522.3 | Ya | Ya | 1,124.8 | 21.3 | Sumberlawang, Sragen, Jawa Tengah (node/10951630643) | PointOnSurface vs Centroid GADM 4.1 + perbedaan batas waduk |
| 99 | `33.14.11` | Kabupaten Sragen | Sidoharjo | -7.419783, 110.966965 | -7.422173, 110.967590 | 274.6 | Ya | Ya | 44.8 | 8.7 | Sidoharjo, Sragen, Jawa Tengah (node/10959875449) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 100 | `33.14.16` | Kabupaten Sragen | Mondokan | -7.319352, 110.927928 | -7.319104, 110.929694 | 196.7 | Ya | Ya | 0.2 | 3.2 | Mondokan, Sragen, Jawa Tengah (node/10951630635) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 101 | `33.14.18` | Kabupaten Sragen | Gesi | -7.331300, 111.004453 | -7.328579, 111.006906 | 405.9 | Ya | Ya | 49.1 | 23.7 | Gesi, Sragen, Jawa Tengah (node/10951630642) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 102 | `33.10.04` | Kabupaten Klaten | Bayat | -7.772045, 110.656888 | -7.772041, 110.654873 | 222.0 | Ya | Ya | 115.8 | 28.2 | Bayat, Klaten, Jawa Tengah (node/10959875445) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 103 | `33.10.20` | Kabupaten Klaten | Jatinom | -7.635601, 110.574896 | -7.634107, 110.575222 | 170.0 | Ya | Ya | 175.2 | 6.2 | Jatinom, Klaten, Jawa Tengah (node/10959875438) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 104 | `33.10.06` | Kabupaten Klaten | Trucuk | -7.724178, 110.669356 | -7.725191, 110.670054 | 136.4 | Ya | Ya | 59.6 | 7.2 | Trucuk, Klaten, Jawa Tengah (relation/19213326) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 105 | `33.10.09` | Kabupaten Klaten | Manisrenggo | -7.690969, 110.501806 | -7.686655, 110.498600 | 595.7 | Ya | Ya | 69.3 | 6.7 | Manisrenggo, Klaten, Jawa Tengah (node/10959875441) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 106 | `33.10.05` | Kabupaten Klaten | Cawas | -7.766585, 110.703551 | -7.761672, 110.712796 | 1,155.8 | Ya | Ya | 903.9 | 6.6 | Cawas, Klaten, Jawa Tengah (node/10959875458) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 107 | `33.10.08` | Kabupaten Klaten | Jogonalan | -7.725958, 110.552970 | -7.728557, 110.547149 | 703.5 | Ya | Ya | 222.2 | 6.5 | Jogonalan, Klaten, Jawa Tengah (node/12394389855) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 108 | `33.10.01` | Kabupaten Klaten | Prambanan | -7.748854, 110.511405 | -7.747314, 110.511527 | 171.8 | Ya | Ya | 31.1 | 7.2 | Jogonalan, Klaten, Jawa Tengah (node/12394389855) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 109 | `33.10.21` | Kabupaten Klaten | Kemalang | -7.607282, 110.489190 | -7.610994, 110.488850 | 414.4 | Ya | Ya | 143.6 | 16.1 | Sidorejo, Kemalang, Klaten (relation/3814506) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 110 | `33.10.12` | Kabupaten Klaten | Pedan | -7.695840, 110.704945 | -7.693286, 110.708366 | 471.9 | Ya | Ya | 117.0 | 9.1 | Pedan City, Pedan, Klaten (relation/18797992) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 111 | `33.10.19` | Kabupaten Klaten | Tulung | -7.596423, 110.600584 | -7.598440, 110.604846 | 520.6 | Ya | Ya | 4.2 | 11.5 | Tulung, Klaten, Jawa Tengah (node/10980867062) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 112 | `33.10.10` | Kabupaten Klaten | Karangnongko | -7.670157, 110.553897 | -7.665866, 110.541833 | 1,412.5 | Ya | Ya | 100.6 | 27.5 | Karangnongko, Klaten, Jawa Tengah (node/10959875439) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 113 | `33.10.14` | Kabupaten Klaten | Juwiring | -7.656403, 110.733865 | -7.658643, 110.738160 | 534.9 | Ya | Ya | 71.7 | 18.6 | Juwiring City, Klaten, Jawa Tengah (relation/18883164) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 114 | `33.10.03` | Kabupaten Klaten | Wedi | -7.771027, 110.602086 | -7.771738, 110.600174 | 225.0 | Ya | Ya | 41.6 | 17.9 | Wedi, Klaten, Jawa Tengah (node/10959875444) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 115 | `33.10.11` | Kabupaten Klaten | Ceper | -7.677578, 110.671035 | -7.680365, 110.670348 | 319.0 | Ya | Ya | 198.1 | 13.1 | Ceper, Klaten, Jawa Tengah (relation/19166246) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 116 | `33.10.24` | Kabupaten Klaten | Klaten Utara | -7.690565, 110.616233 | -7.690071, 110.616167 | 55.4 | Ya | Ya | 46.3 | 14.2 | Kalikotes, Klaten, Jawa Tengah (node/12394389856) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 117 | `33.10.18` | Kabupaten Klaten | Karanganom | -7.640801, 110.628122 | -7.644184, 110.634066 | 755.5 | Ya | Ya | 165.1 | 5.8 | Karanganom, Klaten, Jawa Tengah (node/10959875437) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 118 | `33.10.13` | Kabupaten Klaten | Karangdowo | -7.707499, 110.745424 | -7.706451, 110.745024 | 124.6 | Ya | Ya | 90.2 | 9.0 | Tambak, Karangdowo, Klaten (relation/19289468) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 119 | `33.10.15` | Kabupaten Klaten | Wonosari | -7.627914, 110.740466 | -7.626560, 110.743425 | 359.2 | Ya | Ya | 38.9 | 5.8 | Wonosari, Klaten, Jawa Tengah (relation/18699469) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 120 | `33.10.22` | Kabupaten Klaten | Ngawen | -7.668597, 110.610260 | -7.671496, 110.605858 | 582.4 | Ya | Ya | 184.7 | 21.8 | Karanganom, Klaten, Jawa Tengah (node/10959875437) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 121 | `33.10.23` | Kabupaten Klaten | Kalikotes | -7.727450, 110.628343 | -7.726082, 110.624108 | 490.8 | Ya | Ya | 4.0 | 9.1 | Kalikotes, Klaten, Jawa Tengah (node/12394389856) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 122 | `33.10.26` | Kabupaten Klaten | Klaten Selatan | -7.718323, 110.587396 | -7.719880, 110.587933 | 182.9 | Ya | Ya | 49.3 | 17.0 | Wedi, Klaten, Jawa Tengah (node/10959875444) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 123 | `33.10.25` | Kabupaten Klaten | Klaten Tengah | -7.715822, 110.611561 | -7.715666, 110.608323 | 357.2 | Ya | Ya | 21.4 | 13.4 | Kalikotes, Klaten, Jawa Tengah (node/12394389856) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 124 | `33.10.17` | Kabupaten Klaten | Polanharjo | -7.622360, 110.659899 | -7.614246, 110.663707 | 995.1 | Ya | Ya | 83.0 | 14.3 | Polanharjo, Klaten, Jawa Tengah (node/10980867037) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 125 | `33.10.02` | Kabupaten Klaten | Gantiwarno | -7.776510, 110.552968 | -7.777290, 110.559465 | 721.0 | Ya | Ya | 131.0 | 10.3 | Gantiwarno, Klaten, Jawa Tengah (node/10959875443) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 126 | `33.10.16` | Kabupaten Klaten | Delanggu | -7.629072, 110.688859 | -7.628043, 110.691431 | 305.7 | Ya | Ya | 50.0 | 13.1 | Delanggu, Klaten, Jawa Tengah (relation/18644883) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
| 127 | `33.10.07` | Kabupaten Klaten | Kebonarum | -7.699968, 110.560128 | -7.697663, 110.561614 | 304.1 | Ya | Ya | 85.9 | 25.3 | Basin, Klaten, Jawa Tengah (relation/3815210) | PointOnSurface (UTM 49S) vs Centroid GADM 4.1 (WGS84) |
