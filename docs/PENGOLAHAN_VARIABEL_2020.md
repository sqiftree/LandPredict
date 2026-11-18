# Variabel terukur dan peta interaktif Solo Raya

Pengolahan 18 November 2026 menambahkan lima variabel untuk 127 kecamatan tanpa mengubah target atau angka baseline. Tiga variabel memanfaatkan sumber raster baru; dua merupakan normalisasi variabel lama, sehingga bukan lima sumber informasi independen.

| Kolom | Definisi | Status |
| --- | --- | --- |
| built_pct | Luas piksel kelas built-up / luas piksel valid × 100 | ESA WorldCover 2020 v100 |
| cropland_pct | Luas piksel kelas cropland / luas piksel valid × 100 | Pertanian, bukan khusus sawah |
| tree_pct | Luas piksel kelas tree cover / luas piksel valid × 100 | Tutupan pohon, bukan khusus taman |
| kepadatan_penduduk_proksi | Penduduk sumber 2020 / luas poligon arsip BIG dalam km² | Proksi; batas historis belum terverifikasi |
| kepadatan_fasum_proksi | Fasum sumber / luas poligon arsip BIG dalam km² | Proksi; perbedaan fasum antarsumber belum selesai |

## Sumber dan metode

Raster: [ESA WorldCover 2020 v100](https://doi.org/10.5281/zenodo.5571936), tile S09E108 dan S09E111 pada bucket publik resmi ESA. URL, SHA-256, ukuran, CRS dan resolusi aktual dicatat di `data/processed/manifest.json`. Data berlisensi CC BY 4.0; © ESA WorldCover project 2020 / Contains modified Copernicus Sentinel data (2020) processed by ESA WorldCover consortium. Dokumentasi akses: https://esa-worldcover.org/en/data-access.

Layer dibaca pada resolusi asli tanpa resampling. Geometri kecamatan digabung berdasarkan kunci dan dua padanan eksplisit yang sudah dicatat proyek. Piksel dipilih jika pusatnya berada dalam poligon (`all_touched=False`). Luas piksel dihitung pada elipsoid WGS84 untuk tiap baris lintang, lalu dijumlah menurut kelas; pembobotan ini menghindari menganggap semua piksel koordinat geografis mempunyai luas identik. Cakupan valid menggunakan luas piksel terpilih sebagai penyebut. Tepian poligon diaproksimasi melalui aturan pusat piksel, bukan exact fractional pixel intersection.

Semua 127 wilayah mempunyai piksel terklasifikasi valid; proporsi valid 100% dalam toleransi pembulatan numerik. Ini kelengkapan kelas raster, **bukan 100% akurasi pemetaan**. Semua 11 kelas disimpan pada kolom `wc_*_pct` dan jumlahnya diperiksa 100%. Tiga kolom utama merupakan alias dari kelas yang bersangkutan, bukan prediktor tambahan berbeda. Kolom `raster_area_km2` adalah luas aproksimasi piksel yang terpilih; `luas_arsip_km2` dihitung dari geometri penuh dalam EPSG:32749 untuk kepadatan.

Geometri berasal dari arsip BIG dengan penanda fitur 20230928 (deskripsi layanan edisi 2022), bukan batas yang telah dibuktikan cocok dengan 2020. Titik lama tidak diubah. Geometri visual disederhanakan 40 m **setelah** statistik selesai. GeoJSON tampilan tidak boleh dipakai mengganti geometri analisis.

ATLAS dapat diakses sebagai HTML melalui Python pada sesi ini, tetapi halaman tersebut tidak menyediakan tabel dataset terender yang dapat diekstrak langsung. Tidak ada data angka sawah ATLAS, akses kesehatan, bahaya gunung api, atau ZNT yang diambil. Raster ESA dipakai sebagai alternatif terbuka yang tahunnya jelas, bukan diklaim berasal dari BHUMI.

## Eksplorasi, bukan pengujian model tambahan

`data/processed/korelasi_eksploratif.csv` memuat Pearson dan Spearman terhadap harga pada seluruh 127 observasi. Spearman memakai average ranks untuk ties. Korelasi built-up: Pearson 0,893; Spearman 0,676. Tidak ada p-value, klaim signifikansi, kausalitas, atau hasil model baru. Pengaruh outlier, struktur kelompok, kolinearitas dan ketergantungan spasial belum diuji pada tahap tambahan ini.

Seleksi untuk model berikutnya wajib berada di dalam validasi bersarang; jangan menggunakan hasil eksplorasi seluruh data untuk memilih fitur lalu mengklaim tujuh lipatan luar sebagai validasi independen terhadap keputusan tersebut. Keempat model lama dan CSV hasilnya tetap tidak berubah.

## Reproduksi

Lingkungan pengolahan terpisah dari lingkungan baseline: Python 3.14.4; numpy 2.4.4, shapely 2.1.2, pyproj 3.7.2, rasterio 1.4.4. Dependensi inti dikunci di `requirements-geospatial.txt`.

```bash
python -m pip install -r requirements-geospatial.txt
python scripts/restore_geometry.py
python scripts/download_worldcover.py --output data/raw/worldcover
python scripts/process_supporting_data.py --tiles data/raw/worldcover
python -m unittest discover -s tests -p test_supporting_data.py
```

Downloader memeriksa SHA-256 terhadap manifest sebelum memakai berkas. Raster mentah sekitar 110 MB tidak dimasukkan ke Git. Perubahan hash sumber harus diperiksa; jangan memperbarui manifest hanya agar lolos. `process_supporting_data.py` menghasilkan CSV variabel, CSV korelasi, manifest, dan GeoJSON tampilan. Saat memperbarui situs, salin ke `sites/landpredict-map/dist/` empat berkas keluaran tersebut sebelum publikasi. Paper bagian 6.3 memuat snapshot eksplorasi; jika hasil pemrosesan berubah, tabel tersebut harus diregenerasi/diaudit sebelum paper diterbitkan ulang.

## Visualisasi

Sumber situs: `sites/landpredict-map/dist`. Fitur: layer tematik, filter kabupaten/kota, pencarian kecamatan, zoom/pan, profil saat diklik, legenda kuintil tetap seluruh Solo Raya, diagram sebar, sumber/metode, dan unduhan CSV/manifest. Warna memakai batas kuintil penuh sehingga tidak berubah makna saat wilayah difilter. Peta dasar OSM bersifat opsional dan memerlukan internet. Poligon, data dan pustaka Leaflet disertakan lokal; peta penelitian dapat dijalankan tanpa basemap eksternal.

Untuk membuka lokal, jalankan dari root proyek:

```bash
python3 -m http.server 8000 --directory sites/landpredict-map/dist
```

Buka `http://localhost:8000`. Jangan membuka index.html langsung melalui file:// karena pemuatan GeoJSON memakai fetch. Situs bukan layanan ATR/BPN, tidak menyediakan harga bidang, dan tidak mengakses endpoint BHUMI langsung.

## Pemeriksaan

Lima tes baru memeriksa bobot luas/NoData, pengecualian piksel luar, penolakan kelas tak dikenal, average ranks dan integritas seluruh keluaran. Ketiga kolom sumber tetap sama; 127 kunci unik; 11 proporsi kelas berjumlah 100%. Sintaks JavaScript diperiksa dengan Node. Pemeriksaan visual lintas browser belum dilakukan karena alat browser tidak tersedia pada sesi ini. Paper Word dibangun ulang dan validasi ZIP/XML lulus; eksperimen model tidak dilatih ulang.

Salinan portabel yang disertakan ke repository LandPredict berada di `web/landpredict`; direktori `sites/` merupakan checkout terpisah untuk layanan Sites. Untuk menjalankan salinan GitHub gunakan `python3 -m http.server 8000 --directory web/landpredict`.
