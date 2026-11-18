# LandPredict

Estimasi harga tanah rata-rata per m² pada **127 kecamatan di Solo Raya, tahun 2020**, menggunakan regresi linear, K-Nearest Neighbors (KNN), Decision Tree, dan Geographically Weighted Regression (GWR).

**[Buka atlas interaktif](https://sqiftree.github.io/LandPredict/)** · [Paper Word](docs/Paper%20Harga%20Tanah%20Solo%20Raya.docx) · [Paper Markdown](docs/Paper%20Harga%20Tanah%20Solo%20Raya.md) · [Dataset pendukung](data/processed/variabel_pendukung_2020.csv)

Proyek ini mendukung penelitian dan presentasi akademik. Unit analisisnya adalah rata-rata kecamatan, bukan bidang tanah atau transaksi individual. Hasilnya tidak digunakan untuk penilaian properti maupun prediksi harga tahun berjalan.

## Pertanyaan penelitian

> Apakah kedekatan geografis membantu memperkirakan rata-rata harga tanah suatu kecamatan ketika seluruh kabupaten/kotanya dikeluarkan dari data latih?

Wilayah penelitian mencakup Kota Surakarta serta Kabupaten Boyolali, Karanganyar, Klaten, Sragen, Sukoharjo, dan Wonogiri. Evaluasi memakai tujuh lipatan luar berdasarkan kabupaten/kota. Standardisasi dan pemilihan parameter dilakukan pada data latih melalui validasi internal. GWR menggunakan bobot Gaussian.

## Status penelitian

| Komponen | Status |
| --- | --- |
| Dataset awal | 127 kecamatan; harga, penduduk, dan fasilitas umum regional dari Lampiran A Salim Aziz |
| Audit transkripsi | 127 kunci dan 381 nilai numerik cocok dengan ekstraksi PDF sumber yang diarsipkan |
| Eksperimen empat model | Selesai dengan **dua prediktor: penduduk dan fasilitas umum regional** |
| Variabel pendukung | Lima variabel tambahan sudah diolah untuk 127 kecamatan |
| Eksplorasi korelasi | Pearson dan Spearman tersedia; belum ada uji signifikansi atau klaim kausal |
| Model dengan variabel tambahan | Belum dilatih dan dievaluasi |
| Atlas interaktif | Aktif di GitHub Pages |
| Batas historis 2020 dan pengukuran primer harga | Belum sepenuhnya terverifikasi |

## Atlas interaktif

**https://sqiftree.github.io/LandPredict/**

Atlas menyediakan pilihan layer harga, tutupan lahan, kepadatan, dan cakupan raster; filter kabupaten/kota; pencarian kecamatan; profil wilayah saat diklik; diagram sebar; serta unduhan CSV dan metadata sumber.

Peta ini merupakan visualisasi penelitian, bukan layanan resmi ATR/BPN dan tidak terhubung langsung ke BHUMI. Poligon dan pustaka Leaflet disertakan dalam situs. Peta dasar OpenStreetMap bersifat opsional dan memerlukan internet.

Untuk menjalankan salinan lokal tanpa memasang pustaka eksperimen:

```bash
python3 -m http.server 8000 --directory web/landpredict
```

Buka `http://localhost:8000`. Gunakan server HTTP; membuka `index.html` langsung melalui `file://` dapat menghalangi pemuatan GeoJSON.

Deployment otomatis menggunakan [GitHub Actions](.github/workflows/pages.yml). Perubahan dalam `web/landpredict` pada branch `main` memicu deployment. [Panduan hosting](docs/DEPLOYMENT_PAGES.md) menjelaskan konfigurasi dan pembaruan situs.

## Hasil eksperimen awal

Metrik berikut berasal dari prediksi uji lintas kabupaten/kota dengan **dua prediktor awal**, bukan lima variabel tambahan.

| Model | MAE (Rp/m²) | RMSE (Rp/m²) |
| --- | ---: | ---: |
| Regresi linear | 739.020 | 1.355.435 |
| KNN | **732.073** | 1.530.233 |
| Decision Tree | 756.462 | 1.449.369 |
| GWR Gaussian | 802.227 | 1.409.692 |

KNN memiliki MAE terendah, sedangkan regresi linear memiliki RMSE terendah. Pada spesifikasi yang diuji, GWR belum memberi keunggulan prediktif yang konsisten. Sebanyak 17 prediksi linear dan 15 prediksi GWR bernilai negatif; nilai tersebut tidak dipotong agar hasil evaluasi tetap transparan.

Setiap model menghasilkan 127 prediksi uji dan tujuh blok evaluasi. Empat model menghasilkan 28 baris hasil per wilayah. MAE dan RMSE dihitung ulang langsung dari prediksi.

- [Hasil empat model dan catatan audit](artifacts/spasial/)
- [Hasil tiga baseline](artifacts/baseline/)
- [Figur dan diagnostik](artifacts/figures/)
- [Ringkasan eksperimen](HASIL_PAPER.md)

## Dataset dan variabel pendukung

### Data awal

[Dataset awal](data/harga_tanah_2020.csv) memuat tahun, kabupaten/kota, kecamatan, penduduk, fasilitas umum regional, harga rata-rata per m², dan rujukan halaman lampiran. Angka ditranskripsi dari [Lampiran A penelitian Salim Aziz, UNS](https://digilib.uns.ac.id/dokumen/download/111483/NzEwODU3/Potensi-Struktur-Ruang-Wilayah-Polisentris-Lampiran_Salim-Aziz.pdf).

Artikel sumber mengatribusikan harga kepada BHUMI ATR/BPN 2020. Namun, arsip layer, jenis harga, sampel, dan metode perataan belum diperoleh. Dataset tidak diklaim sebagai transaksi resmi atau hasil ekstraksi langsung ZNT.

### Lima variabel tambahan yang sudah diolah

| Kolom | Makna dan sumber |
| --- | --- |
| `built_pct` | Persentase tutupan terbangun, ESA WorldCover 2020 v100 |
| `cropland_pct` | Persentase tutupan pertanian, ESA WorldCover 2020 v100; bukan khusus sawah |
| `tree_pct` | Persentase tutupan pohon, ESA WorldCover 2020 v100; bukan khusus taman |
| `kepadatan_penduduk_proksi` | Penduduk 2020 dibagi luas poligon arsip BIG, dalam jiwa/km² |
| `kepadatan_fasum_proksi` | Fasilitas regional dibagi luas poligon arsip BIG, dalam unit/km² |

Tiga proporsi dihitung dari raster asli dengan pemilihan pusat piksel di dalam poligon dan pembobotan luas piksel elipsoid. Persentase menggunakan luas piksel valid sebagai penyebut. Dua kepadatan merupakan normalisasi data lama dan diberi label **proksi** karena batas historis 2020 belum terverifikasi.

Seluruh wilayah memiliki cakupan piksel terklasifikasi valid sebesar 100% dalam toleransi numerik. Angka ini menunjukkan kelengkapan kelas raster, bukan akurasi klasifikasi 100%. Geometri tampilan disederhanakan 40 meter setelah statistik dihitung dari geometri penuh.

Korelasi Spearman proporsi terbangun dengan harga adalah sekitar **0,676** pada seluruh 127 observasi. Hasil ini bersifat eksploratif: belum membuktikan signifikansi, sebab-akibat, atau peningkatan kinerja GWR.

- [CSV variabel pendukung](data/processed/variabel_pendukung_2020.csv)
- [CSV korelasi eksploratif](data/processed/korelasi_eksploratif.csv)
- [Manifest sumber, versi, dan SHA-256](data/processed/manifest.json)
- [Metode pengolahan dan keterbatasan](docs/PENGOLAHAN_VARIABEL_2020.md)
- [Registry 25 kandidat variabel](data/kandidat_variabel.csv) dan [landasan jurnal](docs/PENGEMBANGAN_VARIABEL.md)

Daftar 25 kandidat bukan 25 variabel yang seluruhnya telah terkumpul. Kandidat sawah, akses kesehatan, dan bahaya gunung api dari [penelusuran BHUMI/ATLAS](data/SUMBER_BHUMI.md) belum menjadi kolom observasi. Data tutupan lahan yang sudah diolah berasal dari ESA.

## Sumber dan batas interpretasi

| Sumber | Penggunaan | Batas verifikasi |
| --- | --- | --- |
| Lampiran Aziz | Harga, penduduk, fasilitas regional | Transkripsi cocok; pengukuran primer belum sepenuhnya tervalidasi |
| [BIG KSP Satu Peta](https://kspservices.big.go.id/satupeta/rest/services/PUBLIK/BATAS_WILAYAH/MapServer/3) | Poligon kecamatan dan titik representatif | Penanda fitur 20230928; kesesuaian dengan batas 2020 belum terverifikasi |
| [ESA WorldCover 2020 v100](https://doi.org/10.5281/zenodo.5571936) | Tutupan lahan | Klasifikasi raster dan pendekatan tepi piksel memiliki ketidakpastian |

Ke-127 titik berada dalam poligon padanannya. Titik dihitung dari geometri, tidak ditentukan oleh harga dan tidak mewakili lokasi transaksi. Tidak ada koordinat tebakan atau proyeksi harga ke tahun lain.

Audit masih mencatat perbedaan total fasilitas terhadap artikel pada tujuh wilayah dan penduduk pada tiga wilayah. Sebanyak 21 rujukan halaman CSV lama bertuliskan A-4, sedangkan nomor cetaknya B-1. [Dataset rujukan yang diperbaiki](artifacts/data_audit/dataset_2020_rujukan_terverifikasi.csv) mempertahankan angka sumber; eksperimen menggunakan CSV awal.

Lihat [audit dataset](data/SUMBER_DATASET.md), [sumber koordinat](data/SUMBER_KOORDINAT.md), [audit ulang eksperimen](docs/AUDIT_ULANG_2026-11-18.md), dan [audit perubahan naskah](docs/AUDIT_CARBON_2026-11-18.md). Kecocokan transkripsi tidak sama dengan validasi pengukuran primer.

## Menjalankan eksperimen

Gunakan Python 3.12 dan lingkungan tersendiri untuk mempertahankan versi baseline. Dependensi inti ada di `requirements.txt`; versi lengkap lingkungan acuan ada di `artifacts/requirements-resolved.txt`.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python -m tanah run --output hasil/baseline
python -m tanah verify hasil/baseline
python -m tanah run --koordinat data/koordinat.csv --output hasil/spasial
python -m tanah verify hasil/spasial --spasial
```

Di Windows, buat lingkungan dengan `py -3.12 -m venv .venv` dan gunakan `.venv\Scripts\python.exe` sebagai pengganti `python`.

Koordinat arsip tersedia sehingga menjalankan model tidak memerlukan GDAL. Menghitung ulang titik dari poligon memerlukan `ogr2ogr` dengan dukungan GeoJSON, GPKG, dan SQLite.

### Reproduksi penuh dengan Docker

```bash
docker build -t gwr-solo-raya:local .
docker run --rm --network none --user "$(id -u):$(id -g)" \
  -v "$PWD:/app" -w /app gwr-solo-raya:local python scripts/reproduce.py
```

Build image membutuhkan jaringan. Pipeline eksperimen berjalan tanpa jaringan dari arsip lokal: memulihkan GeoJSON, menjalankan baseline, menghitung titik, mengaudit geometri, menjalankan GWR, memeriksa kesetaraan hasil, serta membuat figur. `hasil/` adalah keluaran eksekusi; `artifacts/` menyimpan hasil acuan. Pipeline ini tidak mengunduh atau mengolah WorldCover.

### Mengolah ulang variabel tambahan

Gunakan lingkungan terpisah; jangan mengganti dependensi baseline dengan dependensi pengolahan geospasial. Pengolahan ini telah dijalankan dengan Python 3.14.4.

```bash
python3.14 -m venv .venv-geo
source .venv-geo/bin/activate
python -m pip install -r requirements-geospatial.txt
python scripts/restore_geometry.py
python scripts/download_worldcover.py --output data/raw/worldcover
python scripts/process_supporting_data.py --tiles data/raw/worldcover
python -m unittest discover -s tests -p test_supporting_data.py
```

Unduhan dua tile sekitar 110 MB diperiksa terhadap SHA-256 manifest. Raster mentah tidak disertakan ke Git. Salin empat keluaran dalam `data/processed/` ke `web/landpredict/` sebelum memperbarui atlas; pemeriksaan deployment menolak salinan yang tidak cocok.

## Verifikasi dan pembaruan paper

Tes protokol model dijalankan pada lingkungan baseline setelah hasil eksperimen tersedia:

```bash
python -m unittest discover -s tests -p test_protocol.py
python -m unittest discover -s tests -p test_dataset_audit.py
python -m unittest discover -s tests -p test_manuscript_verification.py
python scripts/check_regression.py artifacts/baseline hasil/baseline
python scripts/check_regression.py artifacts/spasial hasil/spasial
```

Tes pengolahan tambahan memakai lingkungan geospasial pada bagian sebelumnya. Untuk situs, jalankan:

```bash
python3 scripts/check_web_export.py
node --check web/landpredict/app.js
```

Pemeriksaan ini memvalidasi aset relatif, 127 kunci wilayah, hash dan kesesuaian ekspor, serta sintaks JavaScript. Pemeriksaan visual lintas browser belum dilakukan. Jalankan verifikasi Python tanpa opsi `-O`.

Setelah menjalankan pipeline lengkap dan meninjau hasil serta figur:

```bash
python scripts/publish_artifacts.py
python scripts/build_manuscript.py
```

`publish_artifacts.py` memperbarui snapshot hasil; jalankan hanya setelah meninjau perubahan. Generator memakai `docs/paper_template.md` untuk menghasilkan Markdown dan Word. Narasi serta tabel eksplorasi bagian 6.3 harus ditinjau jika data atau metode berubah. Verifikasi CSV pada generator tidak berarti pelatihan model telah dijalankan ulang.

## Struktur repository

```text
tanah/                      Model, validasi bersarang, verifikasi, dan geometri
scripts/                    Reproduksi, audit, pengolahan raster, dan generator paper
tests/                      Tes protokol, audit, dan pengolahan data
data/harga_tanah_2020.csv    Dataset awal eksperimen
data/koordinat.csv          Titik representatif 127 kecamatan
data/processed/             Variabel tambahan, korelasi, GeoJSON, dan manifest
artifacts/                  Snapshot hasil model, audit, dan figur
docs/                       Paper, rancangan variabel, audit, dan panduan deployment
web/landpredict/            Situs statis yang diterbitkan ke GitHub Pages
.github/workflows/          Pemeriksaan dan deployment atlas
```

Skrip CLI lama tetap tersedia sebagai adapter. Arsip geometri BIG disimpan dalam gzip dengan hash untuk pemulihan. PDF sumber lokal tidak diterbitkan bersama repository. Checkout layanan Sites terdahulu terpisah; GitHub Pages menggunakan `web/landpredict`.

## Penggunaan data dan atribusi

ESA WorldCover menggunakan lisensi **CC BY 4.0**. Atribusi: © ESA WorldCover project 2020 / Contains modified Copernicus Sentinel data (2020) processed by ESA WorldCover consortium. Lisensi ini berlaku untuk produk ESA, bukan otomatis seluruh sumber dalam repository. Leaflet menyertakan [lisensinya sendiri](web/landpredict/LEAFLET-LICENSE.txt); peta dasar opsional menggunakan atribusi OpenStreetMap.

Pengembangan berikutnya memprioritaskan audit primer harga, verifikasi batas historis, pemeriksaan kolinearitas, dan evaluasi variabel tambahan dalam validasi bersarang. Tidak ada jaminan seluruh kandidat signifikan atau penambahan variabel meningkatkan akurasi.
